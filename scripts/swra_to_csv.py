"""
Turn an STLA SWRA report (xlsx) into traceability_source.csv, the flat input that
scripts/build_traceability.py reads.

Usage:
    python scripts/swra_to_csv.py STLA_SWRA_Report-CarPlay-R10.xlsx [out.csv]

Only the "CPAA Analysis Report" sheet is read. Its header sits on row 8; the columns
used are (1-based): 1 SWE-Requirement ID, 3 Requirement Title, 33 Categorization,
34 Sub Categorization, 35 Priority, 39 FROP Category, 40 Owner(责任人),
42/43 new/existing SWE1 Jira ID, 44/45 new/existing SWE2 Jira ID. Everything else in
the report is review commentary the dashboard does not use.

Rerun this whenever a new SWRA revision arrives, commit the regenerated CSV, and the
next Actions run picks the new requirements up with live Jira status.
"""
import csv
import re
import sys

try:
    import openpyxl
except ImportError:  # pragma: no cover - dependency hint
    sys.exit("openpyxl is required: pip install openpyxl")

SHEET = "CPAA Analysis Report"
HEADER_ROW = 8
KEY = re.compile(r"[A-Z][A-Z0-9]+-\d+")
COLS = {"reqid": 1, "title": 3, "cat": 33, "sub": 34, "prio": 35, "frop": 39, "owner": 40}
SWE1_COLS = (42, 43)
SWE2_COLS = (44, 45)


def cell(ws, row, col):
    v = ws.cell(row, col).value
    return "" if v is None else str(v).strip()


def keys(ws, row, cols):
    found = []
    for c in cols:
        for k in KEY.findall(cell(ws, row, c)):
            if k not in found:
                found.append(k)
    return " ".join(found)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip())
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "traceability_source.csv"

    wb = openpyxl.load_workbook(src, data_only=True)
    if SHEET not in wb.sheetnames:
        sys.exit(f"sheet {SHEET!r} not found in {src} (has: {', '.join(wb.sheetnames)})")
    ws = wb[SHEET]

    rows = []
    for r in range(HEADER_ROW + 1, ws.max_row + 1):
        swe1 = keys(ws, r, SWE1_COLS)
        swe2 = keys(ws, r, SWE2_COLS)
        if not (swe1 or swe2):
            continue  # commentary / spacer rows carry no ticket at all
        rows.append({
            "owner": cell(ws, r, COLS["owner"]),
            "reqid": cell(ws, r, COLS["reqid"]).replace("\n", " / "),
            "title": cell(ws, r, COLS["title"]),
            "cat": cell(ws, r, COLS["cat"]),
            "sub": cell(ws, r, COLS["sub"]),
            "prio": cell(ws, r, COLS["prio"]),
            "frop": cell(ws, r, COLS["frop"]),
            "swe1": swe1,
            "swe2": swe2,
        })

    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["owner", "reqid", "title", "cat", "sub", "prio", "frop", "swe1", "swe2"])
        w.writeheader()
        w.writerows(rows)

    owners = len({r["owner"] for r in rows if r["owner"]})
    print(f"Wrote {out}: {len(rows)} requirement rows, {owners} owners, "
          f"{len({k for r in rows for k in r['swe1'].split()})} SWE1, "
          f"{len({k for r in rows for k in r['swe2'].split()})} SWE2")


if __name__ == "__main__":
    main()

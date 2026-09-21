"""
Turn an STLA SWRA report (xlsx) into a traceability CSV, the flat input that
scripts/build_traceability.py reads (after merging every report's CSV together —
see scripts/merge_traceability_csv.py or just concatenate rows, keeping one header).

Usage:
    python scripts/swra_to_csv.py STLA_SWRA_Report-CarPlay-R10.xlsx [out.csv] [--feature "CarPlay"]
    python scripts/swra_to_csv.py STLA_SWRA_Report-AndroidAuto-HUIG4.5.2.xlsx [out.csv]

Reads whichever sheet's name ends in "Analysis Report" (case-insensitive) — the
CarPlay report calls it "CPAA Analysis Report", the Android Auto one "AA Analysis
Report", but the column layout is identical either way. Pass --sheet to override.
Its header sits on row 8; the columns used are (1-based): 1 SWE-Requirement ID,
3 Requirement Title, 33 Categorization, 34 Sub Categorization, 35 Priority,
39 FROP Category, 40 Owner(责任人), 42/43 new/existing SWE1 Jira ID, 44/45
new/existing SWE2 Jira ID. Everything else in the report is review commentary the
dashboard does not use.

Every row is tagged with a "feature" column (CarPlay / Android Auto / iPod) so the
Traceability tab can tell rows from different reports apart once they're merged into
one CSV. --feature overrides the guess; otherwise it's inferred from the filename
(a "-CarPlay-" / "-AndroidAuto-" / "-iPod-" segment), defaulting to "CarPlay" if
nothing matches (that was the only report that existed before this tag was added).

Rerun this whenever a new SWRA revision arrives, merge the resulting CSV into
traceability_source.csv (replacing just that feature's old rows), commit it, and the
next Actions run picks the new requirements up with live Jira status.
"""
import csv
import re
import sys

try:
    import openpyxl
except ImportError:  # pragma: no cover - dependency hint
    sys.exit("openpyxl is required: pip install openpyxl")

HEADER_ROW = 8
KEY = re.compile(r"[A-Z][A-Z0-9]+-\d+")
COLS = {"reqid": 1, "title": 3, "cat": 33, "sub": 34, "prio": 35, "frop": 39, "owner": 40}
SWE1_COLS = (42, 43)
SWE2_COLS = (44, 45)
FEATURE_HINTS = [
    (re.compile(r"androidauto", re.I), "Android Auto"),
    (re.compile(r"carplay", re.I), "CarPlay"),
    (re.compile(r"ipod", re.I), "iPod"),
]


def guess_feature(filename):
    for pattern, feature in FEATURE_HINTS:
        if pattern.search(filename):
            return feature
    return "CarPlay"


def find_sheet(wb, override=None):
    if override:
        if override not in wb.sheetnames:
            sys.exit(f"sheet {override!r} not found (has: {', '.join(wb.sheetnames)})")
        return wb[override]
    for name in wb.sheetnames:
        if name.strip().lower().endswith("analysis report"):
            return wb[name]
    sys.exit(f"no sheet ending in 'Analysis Report' found (has: {', '.join(wb.sheetnames)})")


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
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__.strip())
    src = args[0]
    out = args[1] if len(args) > 1 else "traceability_source.csv"

    feature = None
    sheet_override = None
    opts = sys.argv[1:]
    for i, a in enumerate(opts):
        if a == "--feature" and i + 1 < len(opts):
            feature = opts[i + 1]
        if a == "--sheet" and i + 1 < len(opts):
            sheet_override = opts[i + 1]
    if not feature:
        feature = guess_feature(src)

    wb = openpyxl.load_workbook(src, data_only=True)
    ws = find_sheet(wb, sheet_override)

    rows = []
    for r in range(HEADER_ROW + 1, ws.max_row + 1):
        swe1 = keys(ws, r, SWE1_COLS)
        swe2 = keys(ws, r, SWE2_COLS)
        if not (swe1 or swe2):
            continue  # commentary / spacer rows carry no ticket at all
        rows.append({
            "feature": feature,
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
        w = csv.DictWriter(f, fieldnames=["feature", "owner", "reqid", "title", "cat", "sub", "prio", "frop", "swe1", "swe2"])
        w.writeheader()
        w.writerows(rows)

    owners = len({r["owner"] for r in rows if r["owner"]})
    print(f"Wrote {out}: {len(rows)} requirement rows (feature={feature}), {owners} owners, "
          f"{len({k for r in rows for k in r['swe1'].split()})} SWE1, "
          f"{len({k for r in rows for k in r['swe2'].split()})} SWE2")


if __name__ == "__main__":
    main()

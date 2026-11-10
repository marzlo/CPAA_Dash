#!/usr/bin/env python3
"""Turn the CarPlay Facets and Android Auto PCTS result workbooks into pretest_cases.json.

One workbook per platform per round, written by the test team and dropped into the repo
root. Both are optional: the dashboard's Pretest tab falls back to what it showed before
if this file is missing, so a round that only has one of the two still builds.

The workbooks are hand-maintained, so the parser is written to survive them:

  * the header row is found by its labels, not by its row number — rows get inserted
    above it;
  * header rows repeat part-way down a sheet (the BugList sheets do), and a repeat must
    not become a test case or a bug called "Bug ID";
  * the Test Section cell is only filled on the first row of a run, so it carries down;
  * results arrive in mixed case ("pass" vs "Pass") and with underscores
    ("Not_applicable"), so they are normalised to one spelling.

Rates: Pass/Fail/Block are the executed outcomes. N/A and Not executed are counted and
reported, but kept OUT of the denominator — AA has 299 N/A and 92 not executed, and
putting those in the denominator makes a tab that has not been run look like one that
failed. The dashboard shows coverage separately for that reason.

Run: python3 scripts/build_pretest.py      (from the repo root)
"""
import datetime
import glob
import json
import os
import re
import sys

try:
    import openpyxl
except ImportError:  # pragma: no cover - the CI image installs it
    print("build_pretest: openpyxl is not installed; skipping", file=sys.stderr)
    openpyxl = None

OUT = os.environ.get("PRETEST_OUT", "pretest_cases.json")

# Each platform: how to find its workbook, and the header labels that identify its
# result sheet. The English sheet is preferred — the Chinese one carries the same rows.
PLATFORMS = [
    {
        "id": "CP",
        "name": "CarPlay",
        "globs": ["*CarPlay*Facets*Test*Case*.xlsx", "*CarPlay*Test*Case*.xlsx"],
        "sheets": ["Test Result-EN", "Test Result"],
        "id_col": "ID",
        "title_col": "Title",
        "bug_col": "Jira",
    },
    {
        "id": "AA",
        "name": "Android Auto",
        "globs": ["*Android*Auto*PCTS*Test*Case*.xlsx", "*Android*Auto*Test*Case*.xlsx"],
        "sheets": ["Test Result-EN", "Test Result"],
        "id_col": "Case ID",
        "title_col": None,
        "bug_col": "BUG",
    },
]

RESULTS = {
    "pass": "Pass",
    "fail": "Fail",
    "block": "Block",
    "blocked": "Block",
    "not_executed": "Not executed",
    "not executed": "Not executed",
    "not start": "Not executed",
    "not_applicable": "N/A",
    "not applicable": "N/A",
    "n/a": "N/A",
    "na": "N/A",
}
EXECUTED = ("Pass", "Fail", "Block")
ORDER = ["Pass", "Fail", "Block", "Not executed", "N/A", "Other"]


def cell(v):
    if v is None:
        return ""
    return re.sub(r"\s+", " ", str(v)).strip()


def norm_result(v):
    s = cell(v).lower()
    if not s:
        return ""
    # "Fail (waiver)" and friends: keep the qualifier out of the bucket but not out of
    # sight — the raw text travels with the case so the table can still show it.
    base = re.sub(r"\s*[\(（].*$", "", s).strip()
    return RESULTS.get(base, RESULTS.get(s, "Other"))


def pick_workbook(patterns):
    """The newest round on disk. Round N is read out of the file name when it is there,
    so dropping Round3 beside Round2 switches over without editing anything."""
    hits = []
    for pat in patterns:
        hits.extend(glob.glob(pat))
    hits = sorted(set(h for h in hits if not os.path.basename(h).startswith("~$")))
    if not hits:
        return None, None

    def round_of(path):
        m = re.search(r"round\s*[-_ ]?(\d+)", os.path.basename(path), re.I)
        return int(m.group(1)) if m else -1

    hits.sort(key=lambda p: (round_of(p), os.path.getmtime(p)))
    best = hits[-1]
    return best, (round_of(best) if round_of(best) >= 0 else None)


def find_header(ws, wanted, limit=12):
    """Row index and column map for the first row carrying the wanted labels."""
    wanted_low = [w.lower() for w in wanted]
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=limit, values_only=True), 1):
        labels = {cell(v).lower().rstrip(",").rstrip(":"): j for j, v in enumerate(row) if cell(v)}
        if all(w in labels for w in wanted_low):
            return i, labels
    return None, None


def read_suite(ws, hrow):
    """The suite and its version sit loose in the first rows ("PCTS 4.5.2",
    "NR1L-Facets 3.9.0(Test Plan …)"). Nicer in a heading than the file name, so it is
    worth picking up — and harmless when it is not there."""
    for row in ws.iter_rows(min_row=1, max_row=max(1, hrow - 1), values_only=True):
        for v in row:
            s = cell(v)
            m = re.search(r"((?:PCTS|Facets)[\s\-]*\d+(?:\.\d+)*)", s, re.I)
            if m:
                return re.sub(r"\s+", " ", m.group(1)).replace("-", " ").strip()
    return ""


def read_cases(ws, spec):
    want = [spec["id_col"], "Test Result", "Test Section"]
    hrow, cols = find_header(ws, want)
    if hrow is None:
        return [], "no header row with " + ", ".join(want)

    def col(name):
        return cols.get(name.lower()) if name else None

    c_id, c_res = col(spec["id_col"]), col("Test Result")
    c_sec, c_title = col("Test Section"), col(spec["title_col"])
    c_bug, c_conn = col(spec["bug_col"]), col("Connection")
    c_tester, c_remark = col("Tester"), col("Remarks") or col("Comment")

    suite = read_suite(ws, hrow)
    out, section, header_sig = [], "", cell(ws.cell(hrow, c_id + 1).value).lower()
    for row in ws.iter_rows(min_row=hrow + 1, values_only=True):
        cid = cell(row[c_id]) if c_id is not None and c_id < len(row) else ""
        if not cid:
            continue
        # A repeated header row part-way down the sheet is not a test case.
        if cid.lower() == header_sig:
            continue
        sec = cell(row[c_sec]) if c_sec is not None and c_sec < len(row) else ""
        if sec:
            section = sec
        raw = cell(row[c_res]) if c_res is not None and c_res < len(row) else ""
        rec = {
            "sec": section,
            "id": cid,
            "res": norm_result(raw) or "Other",
            "raw": raw,
        }
        for key, idx in (("title", c_title), ("conn", c_conn), ("tester", c_tester),
                         ("remark", c_remark)):
            v = cell(row[idx]) if idx is not None and idx < len(row) else ""
            if v:
                rec[key] = v[:300]
        bug = cell(row[c_bug]) if c_bug is not None and c_bug < len(row) else ""
        if bug:
            # The cell holds "NR1LT-5217 [High][CPAA]…" or several keys; keep the keys.
            keys = re.findall(r"[A-Z][A-Z0-9]+-\d+", bug)
            rec["bugs"] = sorted(set(keys)) if keys else []
        out.append(rec)
    return {"cases": out, "suite": suite}, None


def read_bugs(wb, pid):
    if "BugList" not in wb.sheetnames:
        return []
    ws = wb["BugList"]
    hrow, cols = find_header(ws, ["Bug ID"])
    if hrow is None:
        return []
    c_key = cols["bug id"]
    c_sum = cols.get("summary")
    c_n = cols.get("affected case count")
    c_cmt = cols.get("comment")
    out = []
    for row in ws.iter_rows(min_row=hrow + 1, values_only=True):
        key = cell(row[c_key]) if c_key < len(row) else ""
        # The sheets repeat their own header further down; "Bug ID" is not a bug.
        if not key or not re.fullmatch(r"[A-Z][A-Z0-9]+-\d+", key):
            continue
        n = row[c_n] if c_n is not None and c_n < len(row) else None
        out.append({
            "key": key,
            "src": [pid],
            "summary": (cell(row[c_sum]) if c_sum is not None and c_sum < len(row) else "")[:300],
            "cases": int(n) if isinstance(n, (int, float)) else 0,
            "comment": (cell(row[c_cmt]) if c_cmt is not None and c_cmt < len(row) else "")[:300],
        })
    return out


def summarise(cases):
    counts = {k: 0 for k in ORDER}
    for c in cases:
        counts[c["res"] if c["res"] in counts else "Other"] += 1
    ex = sum(counts[k] for k in EXECUTED)
    by_sec = {}
    for c in cases:
        s = by_sec.setdefault(c["sec"] or "(unsectioned)", {k: 0 for k in ORDER})
        s[c["res"] if c["res"] in s else "Other"] += 1
    sections = []
    for name, s in by_sec.items():
        sex = sum(s[k] for k in EXECUTED)
        sections.append({"sec": name, "executed": sex, "total": sum(s.values()),
                         **{k: s[k] for k in ORDER if s[k]},
                         "rate": round(s["Pass"] / sex * 100, 1) if sex else None})
    # Worst first: that is the reading order anybody actually wants. Sections with
    # nothing executed have no rate, so they sort to the end rather than to 0%.
    sections.sort(key=lambda x: (x["rate"] is None, x["rate"] if x["rate"] is not None else 0,
                                 -x["executed"]))
    return {"counts": counts, "executed": ex, "total": len(cases), "sections": sections}


def main():
    if openpyxl is None:
        return 0
    platforms, bugs, rounds = {}, {}, []
    for spec in PLATFORMS:
        path, rnd = pick_workbook(spec["globs"])
        if not path:
            print(f"Pretest: no workbook for {spec['id']} (looked for {spec['globs'][0]}) "
                  f"— that platform is left out")
            continue
        wb = openpyxl.load_workbook(path, data_only=True)
        sheet = next((s for s in spec["sheets"] if s in wb.sheetnames), None)
        if sheet is None:
            print(f"Pretest: {os.path.basename(path)} has no result sheet "
                  f"({', '.join(spec['sheets'])}) — skipped")
            continue
        parsed, err = read_cases(wb[sheet], spec)
        if err:
            print(f"Pretest: {os.path.basename(path)}/{sheet}: {err} — skipped")
            continue
        cases = parsed["cases"]
        if rnd is not None:
            rounds.append(rnd)
        for b in read_bugs(wb, spec["id"]):
            hit = bugs.get(b["key"])
            if hit:
                hit["src"] = sorted(set(hit["src"]) | set(b["src"]))
                hit["cases"] += b["cases"]
                hit["summary"] = hit["summary"] or b["summary"]
                hit["comment"] = hit["comment"] or b["comment"]
            else:
                bugs[b["key"]] = b
        stats = summarise(cases)
        platforms[spec["id"]] = {
            "id": spec["id"], "name": spec["name"], "round": rnd,
            "source": os.path.basename(path), "sheet": sheet,
            "suite": parsed["suite"],
            "cases": cases, **stats,
        }
        c = stats["counts"]
        rate = (c["Pass"] / stats["executed"] * 100) if stats["executed"] else 0
        print(f"Pretest {spec['id']}: {stats['total']} cases from {os.path.basename(path)} — "
              f"executed {stats['executed']} (Pass {c['Pass']} / Fail {c['Fail']} / "
              f"Block {c['Block']} = {rate:.1f}% pass), "
              f"N/A {c['N/A']}, not executed {c['Not executed']}")
        if c["Other"]:
            odd = sorted({x["raw"] for x in cases if x["res"] == "Other" and x["raw"]})
            print(f"Pretest {spec['id']}: {c['Other']} case(s) with an unrecognised result "
                  f"{odd[:6]} — they are shown but left out of every rate")

    if not platforms:
        print("Pretest: no workbooks found; pretest_cases.json was NOT written")
        return 0

    out = {
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "round": max(rounds) if rounds else None,
        "platforms": platforms,
        "bugs": sorted(bugs.values(), key=lambda b: (-b["cases"], b["key"])),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    both = [b["key"] for b in out["bugs"] if len(b["src"]) > 1]
    print(f"Pretest: {len(out['bugs'])} bug(s) across both workbooks"
          + (f", {len(both)} in both ({', '.join(both[:5])})" if both else "")
          + f"\nWrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

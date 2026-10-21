"""
Build schedule.json from the CPAA certification Gantt workbook.

Input
  NR1L_CPAA_Certification.xlsx   the two certification sheets, columns = weeks,
                                 rows = tasks. A task's span is drawn with cell
                                 fills; milestone words (Submit / Approval /
                                 Re-Submit / Round 1 / Issue Fix / ...) sit inside
                                 those cells. Override with SCHEDULE_XLSX.

Output
  schedule.json                  read by gen_dashboard.py to render the Schedule tab

The workbook's own date row (row 3) is NOT trusted: the file carries year typos —
week 1 of the first block is written 2026-12-29 when it means 2025-12-29, and the
whole second block is written 2026 when it means 2027 (37 columns in all). The week
*sequence* is contiguous and correct, so every column's Monday is derived from a
single anchor instead, which reproduces each correct date and silently fixes the
typos. Mismatches are reported, so a genuine change to the week axis is not mistaken
for one of the known typos.
"""
import datetime as dt
import json
import os
import re
import sys

import openpyxl

SRC = os.environ.get("SCHEDULE_XLSX", "NR1L_CPAA_Certification.xlsx")
OUT = os.environ.get("SCHEDULE_OUT", "schedule.json")

# Monday of the first week column (ISO 2026-W1). Everything else is this plus n weeks.
ANCHOR = dt.date(2025, 12, 29)

SHEETS = [("CarPlay Certification", "CarPlay"), ("Android Auto Certification", "Android Auto")]

# Fill colour -> what the bar means. Taken from the workbook as it stands; an unknown
# colour falls back to "ours" rather than vanishing from the chart.
KIND_BY_RGB = {
    "FFC60A": "ours",       # our own work
    "8F959E": "supplier",   # hardware / supplier-owned
    "FDDDEF": "resubmit",   # a re-submission cycle
    "F54A45": "final",      # final review / hard gate
}
# Row 4's full-width green band is the project milestone strip, not a task.
SKIP_RGB = {"34C724"}
BLANK_RGB = {"00000000", "FFFFFFFF", "000000", "FFFFFF", None}

# Tasks whose planned end falls before this week index are taken as already finished
# when nobody has said otherwise — the backlog that existed when the tab was first
# built. FROZEN ON PURPOSE: deriving it from today's date would quietly mark a new
# batch of tasks done every week, which is the opposite of tracking them.
# Index 42 is the Monday of 2026-W43, the week the Schedule tab shipped.
ASSUME_DONE_BEFORE = 42


def cell_rgb(cell):
    f = cell.fill
    if not f or f.fill_type != "solid":
        return None
    col = f.start_color
    rgb = getattr(col, "rgb", None)
    if not isinstance(rgb, str):
        return None
    return rgb[-6:].upper()


def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")
    return s or "x"


def parse_sheet(ws, feature):
    cols = [c for c in range(4, ws.max_column + 1) if ws.cell(2, c).value]
    tasks = []
    phase = None
    for r in range(5, ws.max_row + 1):
        b = ws.cell(r, 2).value
        name = ws.cell(r, 3).value
        if b:
            phase = str(b).strip()
        if not name:
            continue
        name = str(name).strip()

        cells = []          # (week index, kind or None, text or None)
        for c in cols:
            cell = ws.cell(r, c)
            rgb = cell_rgb(cell)
            text = cell.value
            text = str(text).strip() if text is not None else None
            if rgb in SKIP_RGB:
                rgb = None
            filled = rgb is not None and rgb not in BLANK_RGB
            if not filled and not text:
                continue
            cells.append((c - 4, KIND_BY_RGB.get(rgb, "ours") if filled else "ours", text))
        if not cells:
            continue

        # Collapse the run of cells into contiguous same-kind segments, so the bar keeps
        # the colour changes the workbook draws (an amber task that ends on a red gate).
        segs = []
        for i, kind, _ in cells:
            if segs and segs[-1]["kind"] == kind and segs[-1]["e"] == i - 1:
                segs[-1]["e"] = i
            else:
                segs.append({"s": i, "e": i, "kind": kind})
        marks = [{"i": i, "text": txt} for i, _, txt in cells if txt]

        tasks.append({
            "feature": feature,
            "phase": phase or "",
            "name": name,
            "s": cells[0][0],
            "e": cells[-1][0],
            "segs": segs,
            "marks": marks,
        })
    return tasks


def main():
    try:
        wb = openpyxl.load_workbook(SRC, data_only=True)
    except FileNotFoundError:
        print(f"No {SRC} — skipping the Schedule tab")
        return

    tasks = []
    for sheet, feature in SHEETS:
        if sheet not in wb.sheetnames:
            print(f"  WARNING: sheet {sheet!r} is not in the workbook, skipping it")
            continue
        tasks.extend(parse_sheet(wb[sheet], feature))

    # The workbook repeats a couple of rows verbatim (CarPlay lists
    # "USB IF & USB Signal Integrity" twice under Hardware Certification with the same
    # span). Identical rows in the same phase are one task, not two.
    seen, deduped, dropped = set(), [], 0
    for t in tasks:
        sig = (t["feature"], t["phase"], t["name"], t["s"], t["e"])
        if sig in seen:
            dropped += 1
            continue
        seen.add(sig)
        deduped.append(t)
    tasks = deduped

    # Stable ids: what the done flags and comments are keyed by, so a rebuild from a new
    # workbook keeps everything anybody has ticked. Only a renamed task loses its note,
    # and that is reported below rather than passing silently.
    used = {}
    for t in tasks:
        base = f"{slug(t['feature'])}|{slug(t['phase'])}|{slug(t['name'])}"
        used[base] = used.get(base, 0) + 1
        t["id"] = base if used[base] == 1 else f"{base}~{used[base]}"

    n_weeks = max((t["e"] for t in tasks), default=0) + 1
    weeks = []
    for i in range(n_weeks):
        d = ANCHOR + dt.timedelta(weeks=i)
        iso = d.isocalendar()
        weeks.append({"i": i, "date": d.isoformat(), "label": f"{iso[0]}-W{iso[1]:02d}"})

    # Report where the workbook's own date row disagrees, so a real change to the axis
    # is not quietly absorbed along with the known year typos.
    bad = 0
    ws = wb[SHEETS[0][0]]
    for c in range(4, ws.max_column + 1):
        if not ws.cell(2, c).value:
            continue
        i = c - 4
        if i >= n_weeks:
            continue
        d = ws.cell(3, c).value
        d = d.date() if isinstance(d, dt.datetime) else d
        if d and d != ANCHOR + dt.timedelta(weeks=i):
            bad += 1

    out = {
        "source": os.path.basename(SRC),
        "built_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "anchor": ANCHOR.isoformat(),
        "assume_done_before": ASSUME_DONE_BEFORE,
        "weeks": weeks,
        "tasks": tasks,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"Wrote {OUT}: {len(tasks)} tasks over {n_weeks} weeks"
          + (f" ({dropped} duplicate row(s) merged)" if dropped else ""))
    print(f"  week axis: {weeks[0]['label']} ({weeks[0]['date']}) .. {weeks[-1]['label']} ({weeks[-1]['date']})")
    if bad:
        print(f"  note: {bad} column(s) in the workbook's date row disagree with the week"
              f" sequence and were overridden — these are the known year typos")
    by_feature = {}
    for t in tasks:
        by_feature[t["feature"]] = by_feature.get(t["feature"], 0) + 1
    print("  tasks by feature:", by_feature)


if __name__ == "__main__":
    sys.exit(main())

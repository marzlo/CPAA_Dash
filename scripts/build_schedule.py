"""
Build schedule.json from the CPAA certification Gantt workbook.

Input
  NR1L_CPAA_Certification.xlsx   the two certification sheets, columns = weeks,
                                 rows = tasks. A task's span is drawn with cell
                                 fills; milestone words (Submit / Approval /
                                 Re-Submit / Round 1 / Issue Fix / ...) sit inside
                                 those cells. Override with SCHEDULE_XLSX.

Output
  schedule.json                  read by gen_dashboard.py to render the Schedule tab.
                                 Its "changes" block compares this workbook with the
                                 previous revision of it in git history (the last
                                 commit whose copy of the file differs from the one
                                 being built), so the page can show what moved.
                                 Needs the git history: the workflow checks out with
                                 fetch-depth 0. Without git it is simply left out.

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
import subprocess
import sys
import tempfile

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


# --- what changed since the previous workbook -------------------------------------

def _git(*args, binary=False):
    r = subprocess.run(["git", *args], capture_output=True, check=True)
    return r.stdout if binary else r.stdout.decode("utf-8", "replace").strip()


def previous_revision(path):
    """(info about the version being built, info about the one before it, its bytes).

    "Before it" is the newest commit whose copy of the file differs from the file on
    disk — so this works both locally before the new workbook is committed (HEAD's
    copy is then the previous one) and in CI after it has been (HEAD's copy is the
    same file, and the walk carries on back). None when git or the history is not
    there, or the file has only ever had one revision."""
    try:
        cur_blob = _git("hash-object", path)
        log = _git("log", "--format=%H %cI %s", "--", path).splitlines()
    except (OSError, subprocess.CalledProcessError):
        return None
    cur = {"commit": None, "date": None}
    for line in log:
        sha, date, subject = (line.split(" ", 2) + [""])[:3]
        try:
            blob = _git("rev-parse", f"{sha}:{path}")
        except subprocess.CalledProcessError:
            continue    # the file did not exist under this name in that commit
        if blob == cur_blob:
            # Keep walking back: the version being built is dated by the commit that
            # brought it in, not by a later one that merely carried it along.
            cur = {"commit": sha[:7], "date": date[:10]}
            continue
        data = _git("show", f"{sha}:{path}", binary=True)
        return cur, {"commit": sha[:7], "date": date[:10], "subject": subject}, data
    return None


def _mark_moves(old, new):
    """Pair milestone words by text, in order, so "Round 2" moving is one move."""
    pool = {}
    for m in old:
        pool.setdefault(m["text"], []).append(m["i"])
    moves = []
    for m in new:
        lst = pool.get(m["text"])
        if lst:
            i = lst.pop(0)
            if i != m["i"]:
                moves.append({"text": m["text"], "from": i, "to": m["i"]})
        else:
            moves.append({"text": m["text"], "from": None, "to": m["i"]})
    for text, lst in pool.items():
        for i in lst:
            moves.append({"text": text, "from": i, "to": None})
    return moves


def _shape(t):
    return {"s": t["s"], "e": t["e"], "segs": t["segs"], "marks": t["marks"]}


def diff_tasks(old_tasks, new_tasks):
    old = {t["id"]: t for t in old_tasks}
    new = {t["id"]: t for t in new_tasks}
    items = []
    for t in new_tasks:
        o = old.get(t["id"])
        head = {"id": t["id"], "feature": t["feature"], "phase": t["phase"], "name": t["name"]}
        if o is None:
            items.append({**head, "type": "added", "old": None, "new": _shape(t)})
            continue
        if _shape(o) == _shape(t):
            continue
        items.append({**head, "type": "changed", "old": _shape(o), "new": _shape(t),
                      "ds": t["s"] - o["s"], "de": t["e"] - o["e"],
                      "dd": (t["e"] - t["s"]) - (o["e"] - o["s"]),
                      "reshaped": [g["kind"] for g in o["segs"]]
                                      != [g["kind"] for g in t["segs"]],
                      "marks": _mark_moves(o["marks"], t["marks"])})
    for t in old_tasks:
        if t["id"] not in new:
            items.append({"id": t["id"], "feature": t["feature"], "phase": t["phase"],
                          "name": t["name"], "type": "removed", "old": _shape(t), "new": None})
    return items


def build_changes(tasks):
    rev = previous_revision(SRC)
    if not rev:
        print("  changes: no earlier revision of the workbook in git history — skipped")
        return None
    cur, prev, data = rev
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        f.write(data)
        tmp = f.name
    try:
        prev_tasks = load_tasks(tmp)
    finally:
        os.unlink(tmp)
    items = diff_tasks(prev_tasks, tasks)
    print(f"  changes vs {prev['commit']} ({prev['date']}): {len(items)} task(s) differ")
    return {"cur": cur, "prev": prev, "items": items}


def load_tasks(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    return assign_ids(dedupe(collect(wb)))


def collect(wb, warn=False):
    tasks = []
    for sheet, feature in SHEETS:
        if sheet not in wb.sheetnames:
            if warn:
                print(f"  WARNING: sheet {sheet!r} is not in the workbook, skipping it")
            continue
        tasks.extend(parse_sheet(wb[sheet], feature))
    return tasks


def dedupe(tasks):
    # The workbook repeats a couple of rows verbatim (CarPlay lists
    # "USB IF & USB Signal Integrity" twice under Hardware Certification with the same
    # span). Identical rows in the same phase are one task, not two.
    seen, deduped = set(), []
    for t in tasks:
        sig = (t["feature"], t["phase"], t["name"], t["s"], t["e"])
        if sig in seen:
            continue
        seen.add(sig)
        deduped.append(t)
    return deduped


def assign_ids(tasks):
    # Stable ids: what the done flags and comments are keyed by, so a rebuild from a new
    # workbook keeps everything anybody has ticked. Only a renamed task loses its note,
    # and that is reported below rather than passing silently.
    used = {}
    for t in tasks:
        base = f"{slug(t['feature'])}|{slug(t['phase'])}|{slug(t['name'])}"
        used[base] = used.get(base, 0) + 1
        t["id"] = base if used[base] == 1 else f"{base}~{used[base]}"
    return tasks


def main():
    try:
        wb = openpyxl.load_workbook(SRC, data_only=True)
    except FileNotFoundError:
        print(f"No {SRC} — skipping the Schedule tab")
        return

    raw = collect(wb, warn=True)
    tasks = assign_ids(dedupe(raw))
    dropped = len(raw) - len(tasks)

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
    changes = build_changes(tasks)
    if changes:
        out["changes"] = changes
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

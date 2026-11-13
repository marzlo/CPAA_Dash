"""
Append today's snapshot to history.json, so gen_dashboard.py can render a
burndown-style trend chart on the Stats tab: not-done / total counts per
SWE2/SWE3/SWE5/Bug overall, plus a per-team breakdown of Bug tickets (the
Stats tab's trend chart plots the latter — Bug not-done count over time, one
line per team).

history.json is a repo-committed file (see refresh-dashboard.yml's "Commit history
snapshot" step) — it is the only piece of state this pipeline carries across runs.
There is no way to backfill days before this script started running: Jira's REST API
only exposes current issue state, not a day-by-day history, so the trend line starts
accumulating from whatever day this was first deployed.

One entry per calendar day (Asia/Taipei, matching the dashboard's displayed "最後更新
日期"): re-running the workflow twice in one day overwrites that day's entry rather than
adding a second one.
"""
import json
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

DATA_PATH = "dashboard_data.json"
HISTORY_PATH = "history.json"
PRETEST_CASES_PATH = "pretest_cases.json"

# Same title rules as gen_dashboard.py's PT_RE_AA / PT_RE_CP (ptBugPlatforms): PCTS
# means Android Auto, Facet(s) CarPlay, and a title naming neither counts on both sides.
PT_RE_AA = re.compile(r"PCTS", re.I)
PT_RE_CP = re.compile(r"Facets?", re.I)

# Same fixed team order as gen_dashboard.py's TEAM_ORDER, so the trend chart's
# per-team lines get a stable, non-cycled color assignment (TEAM_COLORS there).
TEAM_ORDER = ['TS_FW', 'TS_CPAA', 'MDT_System', 'MDT_PM', 'MDT_App', 'MDI_System', 'Unassigned', 'Unknown']


def counts(rows):
    total = len(rows)
    done = sum(1 for r in rows if r["done"])
    return {"total": total, "done": done}


def bugs_by_team(bugs):
    teams = list(TEAM_ORDER) + sorted({r.get("team", "Unknown") for r in bugs} - set(TEAM_ORDER))
    result = {}
    for team in teams:
        rows = [r for r in bugs if r.get("team", "Unknown") == team]
        if rows:
            result[team] = counts(rows)
    return result


def group(bugs, key_of):
    """Counts by an arbitrary key, skipping groups that are empty on this day."""
    result = {}
    for row in bugs:
        result.setdefault(key_of(row), []).append(row)
    return {k: counts(v) for k, v in sorted(result.items())}


def rca_bucket(row):
    """Whether the Root Cause Analysis field has anything written in it.

    "unknown" is for rows built from a CSV export that predates the field being
    collected — it keeps those days visibly separate from days where the answer
    really is "nobody filled it in".
    """
    v = row.get("hasRca")
    if v is None:
        return "unknown"
    return "filled" if v else "empty"


def pretest_counts(data):
    """Today's Pretest bug numbers, counted exactly the way the Pretest tab counts them.

    The ticket list is the tab's ptBugRows(): every bug either Round workbook lists
    (pretest_cases.json) plus every Jira Bug titled PCTS / Facet (data["pretest"]).
    A ticket's status is looked up in the same lists, in the same order, as ptTicket().
    "open" = known to Jira and not done; a key no export carries is "unknown" and is
    left out of open, as the tile does. "all" counts a ticket once even when it sits on
    both platforms, so all.open can be less than CP.open + AA.open.

    These daily numbers are what the tab's weekly trend card reads for every week after
    pretest_trend_backfill.json runs out.

    "open_by_status" breaks the open tickets down by the Jira status they are sitting in,
    so the trend card can stack its week-end bar the same way the backfill does. The
    buckets themselves (blocked-ish red, in-progress yellow, everything else grey) live in
    gen_dashboard.py, not here: recording the raw status names means a status nobody has
    bucketed yet still shows up in the data instead of being silently dropped. Days
    recorded before 2026-11-13 have no open_by_status, and the card draws those weeks as a
    plain total rather than inventing a split.
    """
    try:
        with open(PRETEST_CASES_PATH, encoding="utf-8") as f:
            cases = json.load(f) or {}
    except FileNotFoundError:
        cases = {}

    index = {}
    for name in ("tickets", "bugs", "pretest", "watch", "swe3"):
        for r in data.get(name) or []:
            if r and r.get("key") and r["key"] not in index:
                index[r["key"]] = r

    summaries = {}
    for b in cases.get("bugs") or []:
        summaries[b["key"]] = b.get("summary") or ""
    for r in data.get("pretest") or []:
        summaries.setdefault(r["key"], r.get("summary") or "")

    out = {k: {"total": 0, "open": 0, "unknown": 0, "open_by_status": {}} for k in ("all", "CP", "AA")}
    for key, summary in summaries.items():
        tk = index.get(key)
        title = summary or (tk or {}).get("summary") or ""
        if PT_RE_AA.search(title):
            plats = ["AA"]
        elif PT_RE_CP.search(title):
            plats = ["CP"]
        else:
            plats = ["CP", "AA"]
        for p in ["all"] + plats:
            out[p]["total"] += 1
            if tk is None:
                out[p]["unknown"] += 1
            elif not tk.get("done"):
                out[p]["open"] += 1
                st = tk.get("status") or "(none)"
                out[p]["open_by_status"][st] = out[p]["open_by_status"].get(st, 0) + 1
    for v in out.values():
        v["open_by_status"] = dict(sorted(v["open_by_status"].items()))
    return out


def main():
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    tickets = data.get("tickets", [])
    bugs = data.get("bugs", [])
    today = datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d")

    snapshot = {
        "date": today,
        "swe2": counts([r for r in tickets if r["swe"] == "SWE2"]),
        "swe3": counts([r for r in tickets if r["swe"] == "SWE3"]),
        "swe5": counts([r for r in tickets if r["swe"] == "SWE5"]),
        "bugs": counts(bugs),
        "bugs_by_team": bugs_by_team(bugs),
        # Two further breakdowns so the forecast card's actual bars can be split the
        # same way its forecast bars are. Nothing backfills these: days recorded before
        # this change have only bugs_by_team, and the card says so rather than drawing
        # a zero.
        "bugs_by_rca": group(bugs, rca_bucket),
        "bugs_by_status": group(bugs, lambda r: r.get("status") or "(none)"),
        # Pretest open bugs, CP / AA / both, with the open ones broken down by status
        # (added 2026-11-13). Started 2026-11-10; the weeks before that come from
        # pretest_trend_backfill.json, reconstructed from Jira by hand.
        "pretest": pretest_counts(data),
    }

    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = {}

    history[today] = snapshot

    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=1, sort_keys=True)

    print(f"Recorded snapshot for {today}: {snapshot}")
    print(f"history.json now has {len(history)} day(s) of data")


if __name__ == "__main__":
    main()

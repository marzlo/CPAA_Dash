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
from datetime import datetime
from zoneinfo import ZoneInfo

DATA_PATH = "dashboard_data.json"
HISTORY_PATH = "history.json"

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

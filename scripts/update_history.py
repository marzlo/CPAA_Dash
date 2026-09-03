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

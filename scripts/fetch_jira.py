"""
Fetch CPAA tickets straight from Jira Cloud and write them out as a CSV with the
same column shape as the manual "Export as CSV" that build_data.py already knows
how to read (see cpaa-dashboard skill / build_data.py's IDX_* header lookups).

Required environment variables:
  JIRA_SITE        e.g. "mobiledrivetech.atlassian.net"
  JIRA_EMAIL       the Atlassian account email used to generate the API token
  JIRA_API_TOKEN   an Atlassian API token (https://id.atlassian.com/manage-profile/security/api-tokens)
Optional:
  JIRA_JQL         defaults to "filter=12399" (the saved filter used for the manual CSV export)
  OUT_CSV          defaults to "jira_export.csv"

The Severity custom field id (customfield_10230) was confirmed by inspecting a
live Bug issue's full field payload on 2026-09-01. If Mobile Drive ever changes
that field, update SEVERITY_FIELD_ID below.
"""
import base64
import csv
import json
import os
import urllib.error
import urllib.request

JIRA_SITE = os.environ.get("JIRA_SITE", "mobiledrivetech.atlassian.net")
JIRA_EMAIL = os.environ["JIRA_EMAIL"]
JIRA_API_TOKEN = os.environ["JIRA_API_TOKEN"]
JQL = os.environ.get("JIRA_JQL", "filter=12399")
OUT_CSV = os.environ.get("OUT_CSV", "jira_export.csv")

SEVERITY_FIELD_ID = "customfield_10230"
FIELDS = ["issuetype", "summary", "status", "assignee", "labels", "priority", SEVERITY_FIELD_ID, "created"]

_auth = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode()).decode()
_HEADERS = {
    "Authorization": f"Basic {_auth}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def _post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=_HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise RuntimeError(f"Jira API error {e.code} for {url}:\n{detail}") from e


def fetch_all_issues():
    url = f"https://{JIRA_SITE}/rest/api/3/search/jql"
    issues = []
    next_token = None
    while True:
        body = {"jql": JQL, "maxResults": 100, "fields": FIELDS}
        if next_token:
            body["nextPageToken"] = next_token
        data = _post(url, body)
        page = data.get("issues", [])
        issues.extend(page)
        next_token = data.get("nextPageToken")
        if not next_token or not page:
            break
    return issues


def main():
    issues = fetch_all_issues()
    print(f"Fetched {len(issues)} issues from Jira ({JIRA_SITE}, JQL: {JQL})")

    parsed = []
    max_labels = 0
    for issue in issues:
        f = issue.get("fields", {})
        labels = f.get("labels") or []
        max_labels = max(max_labels, len(labels))
        assignee = f.get("assignee") or {}
        priority = f.get("priority") or {}
        severity = f.get(SEVERITY_FIELD_ID)
        if isinstance(severity, dict):
            severity_value = severity.get("value", "")
        else:
            severity_value = severity or ""
        parsed.append({
            "Issue Type": (f.get("issuetype") or {}).get("name", ""),
            "Issue key": issue.get("key", ""),
            "Summary": f.get("summary") or "",
            "Assignee": assignee.get("displayName", ""),
            "Status": (f.get("status") or {}).get("name", ""),
            "Custom field (Severity)": severity_value,
            "Priority": priority.get("name", ""),
            "Created": f.get("created") or "",
            "Labels": labels,
        })

    max_labels = max(max_labels, 1)
    header = (
        ["Issue Type", "Issue key", "Summary"]
        + ["Labels"] * max_labels
        + ["Assignee", "Status", "Custom field (Severity)", "Priority", "Created"]
    )

    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in parsed:
            labels = row["Labels"]
            label_cells = list(labels) + [""] * (max_labels - len(labels))
            writer.writerow([
                row["Issue Type"], row["Issue key"], row["Summary"],
                *label_cells,
                row["Assignee"], row["Status"], row["Custom field (Severity)"],
                row["Priority"], row["Created"],
            ])

    print(f"Wrote {len(parsed)} rows to {OUT_CSV}")


if __name__ == "__main__":
    main()

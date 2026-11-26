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
# "Root Cause Analysis" on the NR1LT board, confirmed against a live issue's field
# payload on 2026-10-02. It is a rich-text field, so the API hands back an Atlassian
# Document Format tree rather than a string — adf_text() below flattens it. The
# dashboard only asks whether it is filled in, but the text is carried anyway so a
# later feature does not need another pipeline change.
RCA_FIELD_ID = "customfield_10985"
RCA_MAX_CHARS = 300
FIELDS = ["issuetype", "summary", "status", "assignee", "labels", "priority", SEVERITY_FIELD_ID,
          RCA_FIELD_ID, "created", "updated", "reporter", "issuelinks", "duedate", "comment"]
# Jira comments ride along in a JSON file beside the CSV (jira_export.csv ->
# jira_export_comments.json): a thread has no flat CSV shape. Only the newest few per
# ticket are kept, each trimmed, so a long debugging thread cannot bloat the page.
OUT_COMMENTS = os.environ.get("OUT_COMMENTS", os.path.splitext(OUT_CSV)[0] + "_comments.json")
COMMENTS_KEEP = 6
COMMENT_MAX_CHARS = 1200


def adf_text(node):
    """Flattens a rich-text field to plain text.

    Jira returns these as ADF (a nested {type, content, text} tree) on the v3 API, but
    older fields and some migrations hand back a plain string instead — both shapes turn
    up in the same export, so both are handled. Anything else (a number, a select) is
    stringified so a non-empty value is never mistaken for an empty one.
    """
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(adf_text(n) for n in node)
    if isinstance(node, dict):
        ntype = node.get("type")
        if ntype == "hardBreak":
            return "\n"
        # Inline nodes whose words live in attrs rather than text: without these a
        # comment reads "please help" with the person it was addressed to missing.
        attrs = node.get("attrs") or {}
        if ntype == "mention":
            return attrs.get("text") or "@?"
        if ntype in {"inlineCard", "blockCard", "embedCard"}:
            return attrs.get("url") or ""
        if ntype in {"mediaSingle", "mediaGroup", "media"}:
            return "[image]\n" if ntype != "media" else ""
        # A select-list field ({"value": ...}) is not ADF at all; without this it would
        # flatten to "" and a filled-in field would read as empty.
        if "text" not in node and "content" not in node and "value" in node:
            return str(node.get("value") or "")
        text = node.get("text") or ""
        inner = adf_text(node.get("content"))
        # Block-level nodes need a separator or their words run together.
        if ntype in {"paragraph", "listItem", "heading", "blockquote", "codeBlock"}:
            inner += "\n"
        return text + inner
    return str(node)


def linked_issues(fields):
    """Flattens Jira's issuelinks into [{key, rel, status, summary}].

    Jira reports a link from whichever end you asked about, so the same relationship
    appears as "blocks" on one side and "is blocked by" on the other. `rel` is always
    written from the point of view of the issue being exported, which is the direction a
    person reading the dashboard expects.
    """
    out = []
    for link in fields.get("issuelinks") or []:
        ltype = link.get("type") or {}
        for side, label in (("outwardIssue", ltype.get("outward")), ("inwardIssue", ltype.get("inward"))):
            other = link.get(side)
            if not other:
                continue
            f = other.get("fields") or {}
            out.append({
                "key": other.get("key", ""),
                "rel": label or "linked",
                "status": ((f.get("status") or {}).get("name") or ""),
                "summary": f.get("summary") or "",
            })
    return out

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


def _get(url):
    req = urllib.request.Request(url, headers=_HEADERS, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise RuntimeError(f"Jira API error {e.code} for {url}:\n{detail}") from e


def latest_comments(key, field):
    """The newest COMMENTS_KEEP comments, oldest first.

    The search endpoint can hand back only the first page of a long thread, and the
    newest comments are the ones the dashboard needs, so a ticket whose thread came
    back short is asked for again, newest first. A failure there keeps what the search
    gave rather than failing the whole build.
    """
    clist = (field or {}).get("comments") or []
    total = (field or {}).get("total", len(clist))
    if total > len(clist):
        try:
            data = _get(f"https://{JIRA_SITE}/rest/api/3/issue/{key}/comment"
                        f"?orderBy=-created&maxResults={COMMENTS_KEEP}")
            clist = list(reversed(data.get("comments") or []))
        except Exception as e:  # noqa: BLE001 — keep the partial thread
            print(f"  comments for {key}: {e}")
    return total, clist[-COMMENTS_KEEP:]


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
    comments = {}
    max_labels = 0
    for issue in issues:
        f = issue.get("fields", {})
        labels = f.get("labels") or []
        max_labels = max(max_labels, len(labels))
        assignee = f.get("assignee") or {}
        reporter = f.get("reporter") or {}
        priority = f.get("priority") or {}
        severity = f.get(SEVERITY_FIELD_ID)
        if isinstance(severity, dict):
            severity_value = severity.get("value", "")
        else:
            severity_value = severity or ""
        rca = adf_text(f.get(RCA_FIELD_ID)).strip()
        ctotal, clist = latest_comments(issue.get("key", ""), f.get("comment"))
        if clist:
            comments[issue.get("key", "")] = {
                "total": ctotal,
                "items": [{
                    "by": (c.get("author") or {}).get("displayName", ""),
                    "at": c.get("created") or "",
                    "text": adf_text(c.get("body")).strip()[:COMMENT_MAX_CHARS],
                } for c in clist],
            }
        parsed.append({
            "Issue Type": (f.get("issuetype") or {}).get("name", ""),
            "Issue key": issue.get("key", ""),
            "Summary": f.get("summary") or "",
            "Assignee": assignee.get("displayName", ""),
            # Who raised the ticket, and when it last moved. The Bug pipeline does not
            # use either, but the Q&A tab is about questions waiting on an answer, so
            # it needs to know who is waiting and whether anything has happened since.
            "Reporter": reporter.get("displayName", ""),
            "Updated": f.get("updated") or "",
            "Status": (f.get("status") or {}).get("name", ""),
            "Custom field (Severity)": severity_value,
            "Priority": priority.get("name", ""),
            "Created": f.get("created") or "",
            # Carried as JSON inside one cell: a link list has no sane flat CSV shape,
            # and csv's own quoting makes the embedded commas and quotes a non-issue.
            "Linked Issues": json.dumps(linked_issues(f), ensure_ascii=False),
            "Custom field (Root Cause Analysis)": rca[:RCA_MAX_CHARS],
            "Due date": f.get("duedate") or "",
            "Labels": labels,
        })

    max_labels = max(max_labels, 1)
    header = (
        ["Issue Type", "Issue key", "Summary"]
        + ["Labels"] * max_labels
        + ["Assignee", "Reporter", "Status", "Custom field (Severity)", "Priority", "Created",
           "Updated", "Linked Issues", "Custom field (Root Cause Analysis)", "Due date"]
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
                row["Assignee"], row["Reporter"], row["Status"], row["Custom field (Severity)"],
                row["Priority"], row["Created"], row["Updated"], row["Linked Issues"],
                row["Custom field (Root Cause Analysis)"], row["Due date"],
            ])

    print(f"Wrote {len(parsed)} rows to {OUT_CSV}")

    with open(OUT_COMMENTS, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False)
    print(f"Wrote comments for {len(comments)} issues to {OUT_COMMENTS}")


if __name__ == "__main__":
    main()

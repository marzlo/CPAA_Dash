"""
Build traceability.json: requirement -> SWE1 / SWE2 -> SWE3, with live Jira status.

Input
  traceability_source.csv   one row per requirement, produced from the STLA SWRA
                            analysis report by scripts/swra_to_csv.py. Columns:
                            owner, reqid, title, cat, sub, prio, frop, swe1, swe2
                            (swe1/swe2 are space-separated Jira keys, possibly empty)

Output
  traceability.json         read by gen_dashboard.py to render the Traceability tab

Required environment variables (the same ones fetch_jira.py already uses):
  JIRA_EMAIL, JIRA_API_TOKEN
Optional:
  JIRA_SITE                 defaults to mobiledrivetech.atlassian.net
  TRACE_SOURCE_CSV          defaults to traceability_source.csv
  TRACE_OUT_JSON            defaults to traceability.json

A SWE2 counts as "covered" when Jira links it to an issue whose summary carries the
SWE3 tag (【SWE3】 or a bare SWE3 token). SWE1 is fetched too, purely so the tab can
show its status; SWE3 tickets were never found hanging off SWE1 in the 2026-09-15
sweep, but if that ever changes they are picked up from SWE1 links as well.
"""
import base64
import csv
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

JIRA_SITE = os.environ.get("JIRA_SITE", "mobiledrivetech.atlassian.net")
SOURCE_CSV = os.environ.get("TRACE_SOURCE_CSV", "traceability_source.csv")
OUT_JSON = os.environ.get("TRACE_OUT_JSON", "traceability.json")

BATCH = 60           # keys per JQL request; keeps each response comfortably small
SWE_TAG = re.compile(r"【(SWE\d)】")
SWE_TAG_PLAIN = re.compile(r"\bSWE(\d)\b")
STATUS_CATEGORY = {"done": "done", "indeterminate": "progress", "new": "todo"}


def swe_tag(summary):
    """SWE level a ticket's summary declares, e.g. 'SWE3', or None."""
    m = SWE_TAG.search(summary or "")
    if m:
        return m.group(1)
    m = SWE_TAG_PLAIN.search(summary or "")
    return "SWE" + m.group(1) if m else None


def short_title(summary):
    """'CP【SWE2】-【WiFi】-【Foo】-【External】' -> '[WiFi]-[Foo]'."""
    s = re.sub(r"^\s*[A-Za-z]*\s*【SWE\d】\s*-?\s*", "", summary or "")
    s = re.sub(r"-?\s*【External】\s*$", "", s)
    return s.replace("【", "[").replace("】", "]").strip(" -")


def jira_headers():
    email = os.environ["JIRA_EMAIL"]
    token = os.environ["JIRA_API_TOKEN"]
    auth = base64.b64encode(f"{email}:{token}".encode()).decode()
    return {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def post(url, body, headers, attempts=3):
    for attempt in range(1, attempts + 1):
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            # 429/5xx are worth another go; anything else is a real error.
            if e.code in (429, 500, 502, 503, 504) and attempt < attempts:
                time.sleep(3 * attempt)
                continue
            raise RuntimeError(f"Jira API error {e.code} for {url}:\n{detail}") from e
        except urllib.error.URLError as e:
            if attempt < attempts:
                time.sleep(3 * attempt)
                continue
            raise RuntimeError(f"Jira API unreachable: {e}") from e


def fetch_issues(keys, headers):
    """key -> {summary, status, cat, links[]} for every key that still exists."""
    url = f"https://{JIRA_SITE}/rest/api/3/search/jql"
    out = {}
    keys = sorted(set(keys))
    for i in range(0, len(keys), BATCH):
        chunk = keys[i:i + BATCH]
        jql = "key in ({})".format(",".join(chunk))
        next_token = None
        while True:
            body = {"jql": jql, "maxResults": 100,
                    "fields": ["summary", "status", "assignee", "issuelinks"]}
            if next_token:
                body["nextPageToken"] = next_token
            data = post(url, body, headers)
            for issue in data.get("issues", []):
                f = issue.get("fields", {})
                status = f.get("status") or {}
                cat = (status.get("statusCategory") or {}).get("key", "new")
                links = []
                for link in f.get("issuelinks", []) or []:
                    other = link.get("inwardIssue") or link.get("outwardIssue")
                    if not other:
                        continue
                    of = other.get("fields", {})
                    ostatus = of.get("status") or {}
                    links.append({
                        "key": other.get("key"),
                        "summary": of.get("summary") or "",
                        "status": ostatus.get("name", "?"),
                        "cat": STATUS_CATEGORY.get((ostatus.get("statusCategory") or {}).get("key"), "todo"),
                        "type": (link.get("type") or {}).get("name", ""),
                    })
                out[issue["key"]] = {
                    "summary": f.get("summary") or "",
                    "status": status.get("name", "?"),
                    "assignee": (f.get("assignee") or {}).get("displayName") or "",
                    "cat": STATUS_CATEGORY.get(cat, "todo"),
                    "links": links,
                }
            next_token = data.get("nextPageToken")
            if not next_token:
                break
        print(f"  fetched {min(i + BATCH, len(keys))}/{len(keys)} issues", flush=True)
    missing = [k for k in keys if k not in out]
    if missing:
        print(f"  WARNING: {len(missing)} key(s) not found in Jira: {', '.join(missing[:10])}"
              + (" …" if len(missing) > 10 else ""))
    return out


def read_source(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build(rows, issues):
    def ticket(key):
        info = issues.get(key)
        if not info:
            # Key in the report but not in Jira (deleted or mistyped) — keep the row
            # visible rather than dropping it silently.
            return {"k": key, "t": "", "st": "not found", "c": "todo", "a": ""}
        # "a" is the ticket's current Jira assignee, which is a different question from
        # the report's Owner column: Owner says who is responsible for the requirement,
        # assignee says who is holding the ticket today.
        return {"k": key, "t": short_title(info["summary"]), "st": info["status"],
                "c": info["cat"], "a": info.get("assignee") or ""}

    def swe3_of(key):
        info = issues.get(key)
        if not info:
            return []
        seen, out = set(), []
        for link in info["links"]:
            if swe_tag(link["summary"]) == "SWE3" and link["key"] not in seen:
                seen.add(link["key"])
                out.append({"k": link["key"], "t": short_title(link["summary"]),
                            "st": link["status"], "c": link["cat"], "via": link["type"]})
        return out

    out_rows = []
    for r in rows:
        swe1_keys = (r.get("swe1") or "").split()
        swe2_keys = (r.get("swe2") or "").split()
        swe1 = []
        for k in swe1_keys:
            item = ticket(k)
            # SWE3 normally hangs off SWE2; if one is linked to a SWE1 instead, surface
            # it there rather than losing it.
            extra = swe3_of(k)
            if extra:
                item["swe3"] = extra
            swe1.append(item)
        swe2 = []
        for k in swe2_keys:
            item = ticket(k)
            item["swe3"] = swe3_of(k)
            swe2.append(item)
        out_rows.append({
            "owner": (r.get("owner") or "").strip() or "(未指定)",
            "reqid": r.get("reqid", ""), "title": r.get("title", ""),
            "cat": r.get("cat", ""), "sub": r.get("sub", ""),
            "prio": r.get("prio", ""), "frop": r.get("frop", ""),
            "swe1": swe1, "swe2": swe2,
        })
    return out_rows


def main():
    if not os.path.exists(SOURCE_CSV):
        print(f"{SOURCE_CSV} not found — skipping traceability build")
        return 0
    rows = read_source(SOURCE_CSV)
    keys = {k for r in rows for k in (r.get("swe1") or "").split()}
    keys |= {k for r in rows for k in (r.get("swe2") or "").split()}
    print(f"{len(rows)} requirement rows, {len(keys)} SWE1+SWE2 keys to look up")

    issues = fetch_issues(keys, jira_headers())
    out_rows = build(rows, issues)

    covered = sum(1 for r in out_rows for x in r["swe2"] if x["swe3"])
    total_swe2 = len({x["k"] for r in out_rows for x in r["swe2"]})
    data = {
        "generated_at": datetime.date.today().isoformat(),
        "source": os.environ.get("TRACE_SOURCE_LABEL", "STLA SWRA Report · CPAA Analysis Report"),
        "project": os.environ.get("TRACE_PROJECT", "CarPlay R10"),
        "rows": out_rows,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Wrote {OUT_JSON}: {len(out_rows)} rows, {total_swe2} unique SWE2, "
          f"{covered} SWE2->SWE3 links")
    return 0


if __name__ == "__main__":
    sys.exit(main())

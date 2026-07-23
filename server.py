# """
# Jira MCP Server
# ---------------
# Exposes Jira Server / Data Center functionality as MCP tools
# that can be used by Claude, Cursor, VS Code, or any MCP client.

# Tools exposed:
#   - get_incidents        : Fetch all incidents (with optional filters)
#   - get_incident_by_key  : Fetch a single incident by key (e.g. OPS-123)
#   - search_issues        : Run a custom JQL query
#   - add_comment          : Add a comment to an issue
#   - update_status        : Transition an issue to a new status

# Requirements:
#     pip install fastmcp requests python-dotenv

# Run:
#     python server.py                    # stdio mode (for Claude Desktop / local)
#     python server.py --transport sse    # SSE mode (for remote / hosted)
# """

import os
import sys
import csv
import io
import requests
from datetime import datetime
from dotenv import load_dotenv
from fastmcp import FastMCP

# ── Load config ────────────────────────────────────────────────────────────────
load_dotenv()

JIRA_BASE_URL  = os.getenv("JIRA_BASE_URL", "").rstrip("/")
JIRA_EMAIL     = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT   = os.getenv("JIRA_PROJECT_KEY", "")
SSE_HOST       = os.getenv("MCP_HOST", "0.0.0.0")
# Railway injects PORT automatically; fallback to MCP_PORT or 8000
SSE_PORT       = int(os.getenv("PORT") or os.getenv("MCP_PORT", "8000"))

if not all([JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
    print("ERROR: Set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN in your .env file.")
    sys.exit(1)

# ── Jira client helpers ────────────────────────────────────────────────────────
AUTH    = (JIRA_EMAIL, JIRA_API_TOKEN)
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

ISSUE_FIELDS = [
    "summary", "status", "priority", "assignee",
    "reporter", "created", "updated", "resolutiondate", "description", "comment"
]


def jira_get(path: str, params: dict | None = None) -> dict:
    """GET request to Jira REST API."""
    url = f"{JIRA_BASE_URL}/rest/api/2/{path}"
    response = requests.get(url, auth=AUTH, headers=HEADERS, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def jira_post(path: str, payload: dict) -> dict:
    """POST request to Jira REST API."""
    url = f"{JIRA_BASE_URL}/rest/api/2/{path}"
    response = requests.post(url, auth=AUTH, headers=HEADERS, json=payload, timeout=30)
    response.raise_for_status()
    return response.json() if response.content else {}


def format_date(date_str: str) -> str:
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return date_str


def format_issue(issue: dict) -> dict:
    """Flatten a raw Jira issue into a clean dict."""
    f = issue.get("fields", {})
    return {
        "key":         issue.get("key", ""),
        "summary":     f.get("summary", ""),
        "status":      (f.get("status") or {}).get("name", ""),
        "priority":    (f.get("priority") or {}).get("name", ""),
        "assignee":    (f.get("assignee") or {}).get("displayName", "Unassigned"),
        "reporter":    (f.get("reporter") or {}).get("displayName", ""),
        "created":     format_date(f.get("created", "")),
        "updated":     format_date(f.get("updated", "")),
        "resolved":    format_date(f.get("resolutiondate", "")),
        "description": (f.get("description") or "").strip(),
    }


def paginate_jql(jql: str, max_total: int = 500) -> list[dict]:
    """Fetch all issues for a JQL query using pagination."""
    all_issues = []
    start_at   = 0
    page_size  = 100

    while len(all_issues) < max_total:
        data   = jira_get("search", {
            "jql":        jql,
            "startAt":    start_at,
            "maxResults": page_size,
            "fields":     ",".join(ISSUE_FIELDS),
        })
        issues = data.get("issues", [])
        total  = data.get("total", 0)
        all_issues.extend(issues)

        if len(all_issues) >= total or not issues:
            break
        start_at += page_size

    return all_issues


def issues_to_csv(issues: list[dict]) -> str:
    """Convert a list of formatted issues to CSV string."""
    if not issues:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=issues[0].keys())
    writer.writeheader()
    writer.writerows(issues)
    return output.getvalue()


# ── MCP Server ─────────────────────────────────────────────────────────────────
mcp = FastMCP(name="jira-mcp-server")


# ── Tool 1: Get Incidents ──────────────────────────────────────────────────────
@mcp.tool()
def get_incidents(
    project: str = "",
    status: str = "",
    priority: str = "",
    max_results: int = 100,
    output_format: str = "json"
) -> str:
    """
    Fetch incidents from Jira.

    Args:
        project:       Project key to filter by (e.g. 'OPS'). Leave blank for all projects.
        status:        Filter by status (e.g. 'Open', 'In Progress', 'Resolved').
        priority:      Filter by priority (e.g. 'High', 'Critical').
        max_results:   Maximum number of incidents to return (default 100).
        output_format: 'json' or 'csv' (default: json).

    Returns:
        List of incidents as JSON or CSV string.
    """
    conditions = ['issuetype = "Incident"']

    proj = project or JIRA_PROJECT
    if proj:
        conditions.append(f'project = "{proj}"')
    if status:
        conditions.append(f'status = "{status}"')
    if priority:
        conditions.append(f'priority = "{priority}"')

    jql    = " AND ".join(conditions) + " ORDER BY created DESC"
    issues = paginate_jql(jql, max_total=max_results)
    formatted = [format_issue(i) for i in issues]

    if output_format.lower() == "csv":
        return issues_to_csv(formatted)

    import json
    return json.dumps({
        "total":     len(formatted),
        "jql_used":  jql,
        "incidents": formatted
    }, indent=2)


# ── Tool 2: Get Incident by Key ────────────────────────────────────────────────
@mcp.tool()
def get_incident_by_key(issue_key: str) -> str:
    """
    Fetch a single Jira issue by its key.

    Args:
        issue_key: The Jira issue key (e.g. 'OPS-123').

    Returns:
        Issue details as a JSON string.
    """
    import json
    issue     = jira_get(f"issue/{issue_key}", {"fields": ",".join(ISSUE_FIELDS)})
    formatted = format_issue(issue)

    # Include comments
    comments_raw = (issue.get("fields", {}).get("comment") or {}).get("comments", [])
    comments = [
        {
            "author":  (c.get("author") or {}).get("displayName", ""),
            "body":    c.get("body", ""),
            "created": format_date(c.get("created", "")),
        }
        for c in comments_raw
    ]
    formatted["comments"] = comments

    return json.dumps(formatted, indent=2)


# ── Tool 3: Search Issues (custom JQL) ────────────────────────────────────────
@mcp.tool()
def search_issues(
    jql: str,
    max_results: int = 50,
    output_format: str = "json"
) -> str:
    """
    Run a custom JQL query against Jira.

    Args:
        jql:           A valid JQL query string (e.g. 'project = OPS AND status = Open').
        max_results:   Maximum number of results (default 50).
        output_format: 'json' or 'csv'.

    Returns:
        Matching issues as JSON or CSV string.
    """
    import json
    issues    = paginate_jql(jql, max_total=max_results)
    formatted = [format_issue(i) for i in issues]

    if output_format.lower() == "csv":
        return issues_to_csv(formatted)

    return json.dumps({
        "total":   len(formatted),
        "issues":  formatted
    }, indent=2)


# ── Tool 4: Add Comment ────────────────────────────────────────────────────────
@mcp.tool()
def add_comment(issue_key: str, comment: str) -> str:
    """
    Add a comment to a Jira issue.

    Args:
        issue_key: The Jira issue key (e.g. 'OPS-123').
        comment:   The comment text to add.

    Returns:
        Confirmation message with comment ID.
    """
    result = jira_post(f"issue/{issue_key}/comment", {"body": comment})
    comment_id = result.get("id", "unknown")
    return f"Comment added successfully to {issue_key} (comment ID: {comment_id})"


# ── Tool 5: Get Available Transitions ─────────────────────────────────────────
@mcp.tool()
def get_transitions(issue_key: str) -> str:
    """
    Get all available status transitions for a Jira issue.
    Call this before update_status to know valid transition names.

    Args:
        issue_key: The Jira issue key (e.g. 'OPS-123').

    Returns:
        List of available transitions as JSON.
    """
    import json
    data        = jira_get(f"issue/{issue_key}/transitions")
    transitions = [
        {"id": t["id"], "name": t["name"]}
        for t in data.get("transitions", [])
    ]
    return json.dumps(transitions, indent=2)


# ── Tool 6: Update Status ──────────────────────────────────────────────────────
@mcp.tool()
def update_status(issue_key: str, transition_name: str) -> str:
    """
    Transition a Jira issue to a new status.
    Use get_transitions first to see valid transition names for the issue.

    Args:
        issue_key:       The Jira issue key (e.g. 'OPS-123').
        transition_name: The name of the transition (e.g. 'Start Progress', 'Resolve').

    Returns:
        Confirmation message or error if transition not found.
    """
    data        = jira_get(f"issue/{issue_key}/transitions")
    transitions = data.get("transitions", [])

    match = next(
        (t for t in transitions if t["name"].lower() == transition_name.lower()),
        None
    )

    if not match:
        available = [t["name"] for t in transitions]
        return f"Transition '{transition_name}' not found. Available: {available}"

    jira_post(f"issue/{issue_key}/transitions", {"transition": {"id": match["id"]}})
    return f"Successfully transitioned {issue_key} → '{transition_name}'"

# ── Tool 7: Delay tool ──────────────────────────────────────────────────────
@mcp.tool()
def delay_tool(seconds: int) -> str:
    """
    Pauses execution for the given number of seconds.
    Use this tool when explicitly asked to wait or delay for testing purposes.

    Args:
        seconds: Number of seconds to sleep before returning.

    Returns:
        A confirmation message stating how long the tool waited.
    """
    import time

    # Basic safety guard so this can't be abused to hang indefinitely
    max_allowed = 3600  # 1 hour cap, adjust as needed
    if seconds < 0:
        return "Error: seconds must be a non-negative integer."
    if seconds > max_allowed:
        return f"Error: seconds exceeds max allowed ({max_allowed}s)."

    time.sleep(seconds)
    return f"Waited {seconds} seconds."

# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    transport = "stdio"
    if "--transport" in sys.argv:
        idx       = sys.argv.index("--transport")
        transport = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "stdio"

    if transport == "sse":
        print(f"Starting Jira MCP Server (SSE) on http://{SSE_HOST}:{SSE_PORT}/mcp")
        print(f"Connect MCP Inspector to: http://{SSE_HOST}:{SSE_PORT}/mcp")
        mcp.run(transport="sse", host=SSE_HOST, port=SSE_PORT)
    else:
        print("Starting Jira MCP Server (stdio)")
        mcp.run(transport="stdio")

# Made with Bob

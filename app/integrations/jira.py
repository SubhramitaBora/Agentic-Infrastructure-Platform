import httpx
import re

from app.config import (
    JIRA_BASE_URL,
    JIRA_EMAIL,
    ATLASSIAN_API_TOKEN,
)


def jira_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def jira_auth():
    return (
        JIRA_EMAIL,
        ATLASSIAN_API_TOKEN,
    )


def create_issue(
    project_key: str,
    summary: str,
    description: str,
    priority: str = "Medium",
    issue_type: str = "Task",
    parent_key: str | None = None,
):
    url = f"{JIRA_BASE_URL}/rest/api/3/issue"

    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", project_key):
        raise ValueError("Invalid Jira project key.")
    if issue_type not in {"Epic", "Story", "Task", "Bug", "Sub-task"}:
        raise ValueError("Unsupported Jira issue type.")
    if issue_type == "Sub-task" and not parent_key:
        raise ValueError("A parent issue key is required to create a Sub-task.")

    # Jira projects can have different issue type schemes. Resolve the actual
    # project issue type and pass its ID to the create endpoint.
    metadata_response = httpx.get(
        f"{JIRA_BASE_URL}/rest/api/3/issue/createmeta/{project_key}/issuetypes",
        params={"startAt": 0, "maxResults": 100},
        headers=jira_headers(),
        auth=jira_auth(),
        timeout=30,
    )
    metadata_response.raise_for_status()
    metadata = metadata_response.json()
    normalized_type = issue_type.casefold().replace("-", "").replace(" ", "")
    matching_type = next(
        (item for item in metadata.get("issueTypes", [])
         if item.get("name", "").casefold().replace("-", "").replace(" ", "") == normalized_type),
        None,
    )
    if matching_type is None:
        available = ", ".join(item.get("name", "") for item in metadata.get("issueTypes", []))
        raise ValueError(
            f"Issue type '{issue_type}' is not available for project {project_key}. "
            f"Available create types: {available or 'none returned'}"
        )

    fields = {
        "project": {"key": project_key},
        "summary": summary,
        "description": {
            "type": "doc",
            "version": 1,
            "content": [{
                "type": "paragraph",
                "content": [{"type": "text", "text": description}],
            }],
        },
        "issuetype": {"id": matching_type["id"]},
        "priority": {"name": priority},
    }
    if parent_key:
        fields["parent"] = {"key": parent_key.strip().upper()}
    payload = {"fields": fields}

    response = httpx.post(
        url,
        json=payload,
        headers=jira_headers(),
        auth=jira_auth(),
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def get_issue(
    issue_key: str,
):
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"

    response = httpx.get(
        url,
        headers=jira_headers(),
        auth=jira_auth(),
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def search_issues(
    project_key: str,
    text: str | None = None,
    status: str | None = None,
    max_results: int = 10,
):
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", project_key):
        raise ValueError("Invalid Jira project key.")
    clauses = [f'project = "{project_key.upper()}"']
    if text:
        escaped_text = text.replace("\\", "\\\\").replace('"', '\\"')
        clauses.append(f'text ~ "{escaped_text}"')
    if status:
        escaped_status = status.replace("\\", "\\\\").replace('"', '\\"')
        clauses.append(f'status = "{escaped_status}"')

    response = httpx.post(
        f"{JIRA_BASE_URL}/rest/api/3/search/jql",
        json={
            "jql": " AND ".join(clauses),
            "maxResults": min(max(max_results, 1), 20),
            "fields": ["summary", "status", "priority", "issuetype"],
        },
        headers=jira_headers(),
        auth=jira_auth(),
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return [
        {
            "issue_key": issue["key"],
            "summary": issue.get("fields", {}).get("summary"),
            "status": (issue.get("fields", {}).get("status") or {}).get("name"),
            "priority": (issue.get("fields", {}).get("priority") or {}).get("name"),
            "issue_type": (issue.get("fields", {}).get("issuetype") or {}).get("name"),
        }
        for issue in data.get("issues", [])
    ]


def update_issue(
    issue_key: str,
    summary: str | None = None,
    description: str | None = None,
    priority: str | None = None,
):
    fields = {}
    if summary is not None:
        fields["summary"] = summary
    if description is not None:
        fields["description"] = {
            "type": "doc",
            "version": 1,
            "content": [{
                "type": "paragraph",
                "content": [{"type": "text", "text": description}],
            }],
        }
    if priority is not None:
        fields["priority"] = {"name": priority}
    if not fields:
        raise ValueError("At least one Jira field must be provided to update.")

    response = httpx.put(
        f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}",
        json={"fields": fields},
        headers=jira_headers(),
        auth=jira_auth(),
        timeout=30,
    )
    response.raise_for_status()
    return {"key": issue_key, "updated_fields": list(fields)}


def transition_issue(issue_key: str, target_status: str) -> dict:
    """Move an issue through one of its currently available workflow transitions."""
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*-\d+", issue_key.strip()):
        raise ValueError("Invalid Jira issue key.")
    if not target_status.strip() or len(target_status) > 100:
        raise ValueError("Target status must be a non-empty value under 100 characters.")

    current_issue = get_issue(issue_key.strip().upper())
    current_status = ((current_issue.get("fields", {}).get("status") or {}).get("name"))
    normalize = lambda value: re.sub(r"[^a-z0-9]+", "", value.casefold())
    if current_status and normalize(current_status) == normalize(target_status):
        return {
            "issue_key": current_issue["key"],
            "previous_status": current_status,
            "status": current_status,
            "transition": None,
            "unchanged": True,
        }

    transitions_response = httpx.get(
        f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key.strip().upper()}/transitions",
        headers=jira_headers(),
        auth=jira_auth(),
        timeout=30,
    )
    transitions_response.raise_for_status()
    transitions = transitions_response.json().get("transitions", [])
    matches = [
        transition for transition in transitions
        if normalize(((transition.get("to") or {}).get("name") or "")) == normalize(target_status)
    ]
    if not matches:
        available = ", ".join(
            f"{item.get('name', 'unnamed')} → {(item.get('to') or {}).get('name', 'unknown')}"
            for item in transitions
        )
        raise ValueError(
            f"Cannot move {issue_key} to '{target_status}' from '{current_status or 'unknown'}'. "
            f"Available transitions: {available or 'none (check workflow permissions and conditions)'}"
        )
    if len(matches) > 1:
        choices = ", ".join(item.get("name", "unnamed") for item in matches)
        raise ValueError(
            f"More than one transition leads to '{target_status}': {choices}. "
            "Please choose a specific transition."
        )

    selected = matches[0]
    transition_response = httpx.post(
        f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key.strip().upper()}/transitions",
        json={"transition": {"id": selected["id"]}},
        headers=jira_headers(),
        auth=jira_auth(),
        timeout=30,
    )
    transition_response.raise_for_status()
    return {
        "issue_key": current_issue["key"],
        "previous_status": current_status,
        "requested_status": (selected.get("to") or {}).get("name"),
        "transition": selected.get("name"),
        "unchanged": False,
    }

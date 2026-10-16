from mcp.server.mcpserver import MCPServer

from app.integrations.jira import (
    create_issue,
    get_issue,
    search_issues,
    transition_issue,
    update_issue,
)
from app.config import JIRA_BASE_URL

mcp = MCPServer("Jira MCP Server")


@mcp.tool()
def create_jira_issue(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
    priority: str = "Medium",
    parent_key: str | None = None,
) -> dict:
    """
    Create an Epic, Story, Task, Bug, or Sub-task in the specified Jira project.
    Sub-tasks require a parent issue key; Stories may optionally be linked to an Epic.
    """

    result = create_issue(
        project_key=project_key,
        issue_type=issue_type,
        summary=summary,
        description=description,
        priority=priority,
        parent_key=parent_key,
    )

    return {
        "status": "success",
        "operation": "create_jira_issue",
        "project_key": project_key,
        "issue_type": issue_type,
        "parent_key": parent_key,
        "issue_key": result["key"],
        "issue_id": result["id"],
        "issue_url": f"{JIRA_BASE_URL.rstrip('/')}/browse/{result['key']}",
    }


@mcp.tool()
def get_jira_issue(
    issue_key: str,
) -> dict:
    """
    Retrieve a Jira issue by its issue key.
    """

    result = get_issue(issue_key)

    fields = result["fields"]

    return {
        "status": "success",
        "operation": "get_jira_issue",
        "issue_key": result["key"],
        "project_key": result["fields"]["project"]["key"],
        "summary": fields.get("summary"),
        "description": fields.get("description"),
        "priority": (
            fields.get("priority", {}).get("name")
            if fields.get("priority")
            else None
        ),
        "issue_type": (
            fields.get("issuetype", {}).get("name")
            if fields.get("issuetype")
            else None
        ),
        "status": (
            fields.get("status", {}).get("name")
            if fields.get("status")
            else None
        ),
    }


@mcp.tool()
def search_jira_issues(
    project_key: str,
    text: str | None = None,
    status: str | None = None,
    max_results: int = 10,
) -> dict:
    """Search Jira issues in a project by text and/or workflow status."""
    return {
        "status": "success",
        "operation": "search_jira_issues",
        "project_key": project_key.upper(),
        "issues": search_issues(project_key, text, status, max_results),
    }


@mcp.tool()
def update_jira_issue(
    issue_key: str,
    summary: str | None = None,
    description: str | None = None,
    priority: str | None = None,
) -> dict:
    """Update a Jira issue's summary, description, or priority."""
    result = update_issue(issue_key, summary, description, priority)
    return {
        "status": "success",
        "operation": "update_jira_issue",
        "issue_key": result["key"],
        "updated_fields": result["updated_fields"],
        "issue_url": f"{JIRA_BASE_URL.rstrip('/')}/browse/{result['key']}",
    }


@mcp.tool()
def transition_jira_issue(issue_key: str, target_status: str) -> dict:
    """Move an issue to a target status through a currently available workflow transition."""
    result = transition_issue(issue_key, target_status)
    return {
        "status": "success",
        "operation": "transition_jira_issue",
        **result,
        "issue_url": f"{JIRA_BASE_URL.rstrip('/')}/browse/{result['issue_key']}",
    }


if __name__ == "__main__":
    mcp.run()

"""Jira specialist backed by the shared bounded agent/tool loop."""

from app.agents.devops_agent import run_agent_loop


async def jira_agent(request: str) -> dict:
    result = await run_agent_loop(request, agent_scope="jira")
    result["agent"] = "jira_agent"
    return result

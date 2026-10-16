"""Confluence specialist backed by the shared bounded agent/tool loop."""

from app.agents.devops_agent import run_agent_loop


async def confluence_agent(request: str) -> dict:
    result = await run_agent_loop(request, agent_scope="confluence")
    result["agent"] = "confluence_agent"
    return result

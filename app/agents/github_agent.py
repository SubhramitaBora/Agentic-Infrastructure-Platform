"""GitHub specialist backed by the shared bounded agent/tool loop."""

from app.agents.devops_agent import run_agent_loop


async def github_agent(request: str) -> dict:
    result = await run_agent_loop(request, agent_scope="github")
    result["agent"] = "github_agent"
    return result

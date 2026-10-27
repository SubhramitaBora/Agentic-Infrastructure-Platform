"""Interactive terminal chat for the DevOps agent."""

import asyncio
import json

from app.agents.devops_agent import devops_agent
from app.llm.client import close_model_client


async def _chat() -> None:
    print("DevOps agent chat. Type 'exit' or 'quit' to stop.")
    try:
        while True:
            try:
                request = input("You> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nChat ended.")
                return

            if request.casefold() in {"exit", "quit"}:
                print("Chat ended.")
                return
            if not request:
                continue

            try:
                result = await devops_agent(request)
            except Exception as exc:
                print(f"Agent request failed: {exc}")
                continue

            answer = result.get("answer")
            if answer:
                print(f"Agent> {answer}")
            else:
                print("Agent>")
                print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        await close_model_client()


def main() -> None:
    asyncio.run(_chat())


if __name__ == "__main__":
    main()

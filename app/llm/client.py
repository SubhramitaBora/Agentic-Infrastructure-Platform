"""Select the model provider used by every agent entry point."""

from app.config import LLM_PROVIDER


def _provider_client():
    if LLM_PROVIDER == "hydra":
        from app.llm import hydra_client

        return hydra_client
    if LLM_PROVIDER == "groq":
        from app.llm import groq_client

        return groq_client
    raise RuntimeError(
        f"Unsupported LLM_PROVIDER '{LLM_PROVIDER}'. Choose 'hydra' or 'groq'."
    )


async def ask_model(prompt: str) -> str:
    """Send a plain-text prompt to the configured model provider."""
    client = _provider_client()
    method = client.ask_hydra if LLM_PROVIDER == "hydra" else client.ask_groq
    return await method(prompt)


async def chat_with_model(messages: list[dict], tools: list[dict]):
    """Send a tool-aware conversation to the configured model provider."""
    client = _provider_client()
    method = client.chat_with_hydra if LLM_PROVIDER == "hydra" else client.chat_with_groq
    return await method(messages, tools)


async def close_model_client() -> None:
    """Close the selected provider's client resources when supported."""
    if LLM_PROVIDER == "hydra":
        from app.llm.hydra_client import close_hydra

        await close_hydra()
    elif LLM_PROVIDER == "groq":
        from app.llm.groq_client import client

        await client.close()


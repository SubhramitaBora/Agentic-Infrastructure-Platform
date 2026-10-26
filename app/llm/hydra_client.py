"""OpenAI-compatible SDK client for the local Hydra LiteLLM endpoint."""

from openai import AsyncOpenAI

from app.config import (
    HYDRA_API_KEY,
    HYDRA_LITELLM_BASE_URL,
    HYDRA_MODEL,
    HYDRA_TIMEOUT,
)


_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client

    if not HYDRA_LITELLM_BASE_URL:
        raise RuntimeError("HYDRA_LITELLM_BASE_URL is not configured.")
    if not HYDRA_MODEL:
        raise RuntimeError("HYDRA_MODEL is not configured.")

    if _client is None:
        base_url = HYDRA_LITELLM_BASE_URL.rstrip("/")
        # The SDK appends /chat/completions itself, so accept the API root or
        # normalize a full chat-completions URL back to that root.
        suffix = "/chat/completions"
        if base_url.endswith(suffix):
            base_url = base_url[: -len(suffix)]

        _client = AsyncOpenAI(
            base_url=base_url,
            # LiteLLM can run without proxy authentication. The SDK requires
            # a non-empty key, so use a local placeholder when no key is set.
            api_key=HYDRA_API_KEY or "local-no-auth",
            timeout=HYDRA_TIMEOUT,
        )
    return _client


async def ask_hydra(prompt: str) -> str:
    """Send a plain-text prompt to Hydra and return its response text."""
    response = await _get_client().chat.completions.create(
        model=HYDRA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content or ""


async def chat_with_hydra(messages: list[dict], tools: list[dict]):
    """Send the agent conversation and available function tools to Hydra."""
    return await _get_client().chat.completions.create(
        model=HYDRA_MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        parallel_tool_calls=False,
        temperature=0,
    )


async def close_hydra() -> None:
    """Close the SDK's HTTP connection pool during application shutdown."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None

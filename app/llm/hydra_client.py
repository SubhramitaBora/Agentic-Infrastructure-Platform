"""Chat-completions client for the local Hydra LiteLLM endpoint."""

import httpx

from app.config import (
    HYDRA_API_KEY,
    HYDRA_LITELLM_BASE_URL,
    HYDRA_MODEL,
    HYDRA_TIMEOUT,
)


def _settings() -> tuple[str, str, dict[str, str]]:
    if not HYDRA_LITELLM_BASE_URL:
        raise RuntimeError("HYDRA_LITELLM_BASE_URL is not configured.")
    if not HYDRA_MODEL:
        raise RuntimeError("HYDRA_MODEL is not configured.")

    base_url = HYDRA_LITELLM_BASE_URL.rstrip("/")
    # Accept either a LiteLLM API root (.../v1) or its chat-completions URL.
    if base_url.endswith("/chat/completions"):
        url = base_url
    else:
        url = f"{base_url}/chat/completions"

    headers = {"Content-Type": "application/json"}
    if HYDRA_API_KEY:
        headers["Authorization"] = f"Bearer {HYDRA_API_KEY}"
    return url, HYDRA_MODEL, headers


async def _chat(payload: dict) -> dict:
    url, _, headers = _settings()
    async with httpx.AsyncClient(timeout=HYDRA_TIMEOUT) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


async def ask_hydra(prompt: str) -> str:
    """Send a plain-text prompt to Hydra and return its response text."""
    _, model, _ = _settings()
    data = await _chat({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    })
    return data["choices"][0]["message"].get("content") or ""


async def chat_with_hydra(messages: list[dict], tools: list[dict]) -> dict:
    """Send the agent conversation and available function tools to Hydra."""
    _, model, _ = _settings()
    return await _chat({
        "model": model,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
        "parallel_tool_calls": False,
        "temperature": 0,
    })

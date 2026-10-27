"""Choose a specialist agent for a single-domain request."""

import re

from app.llm.client import ask_model


def _fallback_route(request: str) -> str:
    text = request.casefold()
    domains = set()
    if re.search(r"\b(jira|issue|epic|story|sub-?task|sprint|project key)\b", text) or re.search(
        r"\b[a-z][a-z0-9_]*-\d+\b", text
    ):
        domains.add("jira")
    if re.search(r"\b(github|pull request|pull-request|repository|repo)\b", text) or re.search(
        r"\b[a-z0-9_.-]+/[a-z0-9_.-]+\b", text
    ):
        domains.add("github")
    if re.search(r"\b(confluence|space|page|folder)\b", text):
        domains.add("confluence")
    return next(iter(domains)) if len(domains) == 1 else "devops"


async def classify_request(request: str) -> str:
    """Classify the request with the configured model provider."""
    prompt = (
        "Choose exactly one destination for this user request. Return only one "
        "lowercase word from: jira, github, confluence, devops. Choose a specialist "
        "when the request is about only that service. Choose devops when it asks "
        "about general infrastructure/operations, multiple services, or is unclear. "
        "Do not execute the request; classify it only.\n\nREQUEST:\n" + request
    )
    try:
        choice = (await ask_model(prompt) or "").strip().casefold()
        match = re.fullmatch(r"(jira|github|confluence|devops)[.!]?", choice)
        destination = match.group(1) if match else _fallback_route(request)
    except Exception:
        destination = _fallback_route(request)

    return destination

"""Deterministic checks for the team's Confluence knowledge-page policy."""
from __future__ import annotations

import re


REQUIRED_HEADINGS = (
    "Overview",
    "Purpose",
    "Key Concepts",
    "How It Works",
    "Example",
    "Common Problems",
    "Related Topics",
)

TITLE_CATEGORIES = {
    "ai/llm": "AI/LLM",
    "rag": "RAG",
    "mcp": "MCP",
    "devops/sre": "DevOps/SRE",
    "sre": "DevOps/SRE",
    "infrastructure": "Infrastructure",
    "integrations": "Integrations",
    "integration": "Integrations",
}

VAGUE_TITLES = {
    "things about ai", "document 1", "untitled", "new page", "notes",
    "misc", "stuff", "overview",
}

ABBREVIATIONS = {
    "RAG": r"(?:RAG\s*\(\s*Retrieval[- ]Augmented Generation\s*\)|Retrieval[- ]Augmented Generation\s*\(\s*RAG\s*\))",
    "MCP": r"(?:MCP\s*\(\s*Model Context Protocol\s*\)|Model Context Protocol\s*\(\s*MCP\s*\))",
    "TTFT": r"(?:TTFT\s*\(\s*Time to First Token\s*\)|Time to First Token\s*\(\s*TTFT\s*\))",
    "KV cache": r"(?:KV cache\s*\(\s*Key[- ]Value cache\s*\)|Key[- ]Value cache\s*\(\s*KV cache\s*\))",
}


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def validate_confluence_page(title: str, headings: list[str], body_text: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    title_clean = title.strip()
    match = re.fullmatch(r"\s*(.+?)\s+[–—-]\s+(.+?)\s*", title_clean)
    if not match:
        findings.append({
            "kind": "page_title",
            "problem": "Title does not follow the required '[Category] – [Specific Topic]' pattern.",
            "suggestion": "Use one approved category, an en dash, and a specific topic, for example 'RAG – RAG Architecture'.",
            "severity": "medium",
        })
    else:
        category, topic = match.group(1).strip().casefold(), match.group(2).strip()
        if category not in TITLE_CATEGORIES:
            findings.append({
                "kind": "page_category",
                "problem": f"'{match.group(1).strip()}' is not one of the approved page categories.",
                "suggestion": "Choose AI/LLM, RAG, MCP, DevOps/SRE, Infrastructure, or Integrations.",
                "severity": "medium",
            })
        if not topic or _normalise(topic) in VAGUE_TITLES:
            findings.append({
                "kind": "page_title",
                "problem": "The title topic is vague or not specific enough.",
                "suggestion": "Name the actual subject, for example 'MCP – MCP Gateway Architecture'.",
                "severity": "medium",
            })

    present = {_normalise(heading) for heading in headings}
    missing = [heading for heading in REQUIRED_HEADINGS if _normalise(heading) not in present]
    if missing:
        findings.append({
            "kind": "required_headings",
            "problem": "Missing required technical-page headings: " + ", ".join(missing) + ".",
            "suggestion": "Add each missing heading and fill it with topic-specific content. If information is unavailable, write 'Not specified' or 'Unknown'.",
            "severity": "medium",
        })

    for abbreviation, expansion_pattern in ABBREVIATIONS.items():
        if re.search(rf"\b{re.escape(abbreviation)}\b", body_text, re.IGNORECASE) and not re.search(
            expansion_pattern, body_text, re.IGNORECASE
        ):
            findings.append({
                "kind": "abbreviation",
                "problem": f"'{abbreviation}' appears without its full term being explained.",
                "suggestion": f"Explain {abbreviation} at first use using its full term in parentheses.",
                "severity": "low",
            })
    return findings

"""Small Confluence Cloud REST API client using the Jira Atlassian token."""
from __future__ import annotations

import httpx
from html import escape

from app.config import ATLASSIAN_API_TOKEN, CONFLUENCE_BASE_URL, CONFLUENCE_EMAIL


def _base_url() -> str:
    if not CONFLUENCE_BASE_URL or not CONFLUENCE_EMAIL or not ATLASSIAN_API_TOKEN:
        raise RuntimeError(
            "Configure CONFLUENCE_BASE_URL, CONFLUENCE_EMAIL and "
            "ATLASSIAN_API_TOKEN in .env."
        )
    return CONFLUENCE_BASE_URL.rstrip("/")


def _request(method: str, path: str, **kwargs) -> dict:
    response = httpx.request(
        method,
        f"{_base_url()}/wiki{path}",
        auth=(CONFLUENCE_EMAIL, ATLASSIAN_API_TOKEN),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=30,
        **kwargs,
    )
    response.raise_for_status()
    return response.json() if response.content else {}


def get_spaces(limit: int = 25) -> list[dict]:
    data = _request("GET", "/api/v2/spaces", params={"limit": min(max(limit, 1), 50)})
    return [
        {"id": s.get("id"), "key": s.get("key"), "name": s.get("name"),
         "type": s.get("type"), "status": s.get("status"),
         "homepage_id": s.get("homepageId")}
        for s in data.get("results", [])
    ]


def search_pages(query: str, space_key: str | None = None, limit: int = 10) -> list[dict]:
    escaped = query.replace("\\", "\\\\").replace('"', '\\"')
    clauses = ['type = page', f'text ~ "{escaped}"']
    if space_key:
        key = space_key.strip().upper()
        if not key.replace("_", "").isalnum():
            raise ValueError("Invalid Confluence space key.")
        clauses.append(f'space = "{key}"')
    data = _request(
        "GET", "/rest/api/search",
        params={"cql": " AND ".join(clauses), "limit": min(max(limit, 1), 25)},
    )
    results = []
    for row in data.get("results", []):
        page = row.get("content", row)
        results.append({
            "id": page.get("id"), "title": page.get("title"),
            "space": (page.get("space") or {}).get("key"),
            "url": (page.get("_links") or {}).get("webui") or row.get("url"),
            "excerpt": row.get("excerpt"),
        })
    return results


def get_page(page_id: str) -> dict:
    data = _request("GET", f"/api/v2/pages/{page_id}", params={"body-format": "storage"})
    body = data.get("body", {}).get("storage", {})
    return {
        "id": data.get("id"), "title": data.get("title"),
        "space_id": data.get("spaceId"), "parent_id": data.get("parentId"),
        "status": data.get("status"), "version": (data.get("version") or {}).get("number"),
        "body": body.get("value", "") if isinstance(body, dict) else "",
        "url": (data.get("_links") or {}).get("webui"),
    }


def create_page(space_id: str, title: str, body: str, parent_id: str | None = None) -> dict:
    if not all(isinstance(value, str) and value.strip() for value in (space_id, title, body)):
        raise ValueError("Space ID, page title, and body are required.")
    existing = _request(
        "GET", f"/api/v2/spaces/{space_id}/pages",
        params={"title": title.strip(), "limit": 25},
    )
    duplicate = next(
        (page for page in existing.get("results", [])
         if str(page.get("title", "")).casefold() == title.strip().casefold()),
        None,
    )
    if duplicate:
        raise ValueError(
            f"A page with this exact title already exists in the space "
            f"(page ID {duplicate.get('id')}). Review the existing page instead of duplicating it."
        )
    payload = {
        "spaceId": space_id,
        "status": "current",
        "title": title.strip(),
        "body": {"representation": "storage", "value": body},
    }
    if parent_id:
        payload["parentId"] = parent_id
    data = _request("POST", "/api/v2/pages", json=payload)
    return {
        "id": data.get("id"), "title": data.get("title"),
        "space_id": data.get("spaceId"), "parent_id": data.get("parentId"),
        "version": (data.get("version") or {}).get("number"),
    }


def create_folder(space_id: str, title: str, parent_id: str | None = None) -> dict:
    if not all(isinstance(value, str) and value.strip() for value in (space_id, title)):
        raise ValueError("Space ID and folder title are required.")
    payload = {"spaceId": space_id, "title": title.strip()}
    if parent_id:
        payload["parentId"] = parent_id
    data = _request("POST", "/api/v2/folders", json=payload)
    return {
        "id": data.get("id"), "title": data.get("title"),
        "space_id": data.get("spaceId"), "parent_id": data.get("parentId"),
    }


def get_folder(folder_id: str) -> dict:
    data = _request("GET", f"/api/v2/folders/{folder_id}")
    return {
        "id": data.get("id"), "title": data.get("title"),
        "space_id": data.get("spaceId"), "parent_id": data.get("parentId"),
        "parent_type": data.get("parentType"),
        "version": (data.get("version") or {}).get("number"),
    }


def get_folder_children(folder_id: str, limit: int = 25) -> list[dict]:
    data = _request(
        "GET", f"/api/v2/folders/{folder_id}/direct-children",
        params={"limit": min(max(limit, 1), 50)},
    )
    return [
        {"id": item.get("id"), "title": item.get("title"),
         "type": item.get("type"), "status": item.get("status"),
         "space_id": item.get("spaceId")}
        for item in data.get("results", [])
    ]


def get_inline_comments(page_id: str, limit: int = 50) -> list[dict]:
    data = _request(
        "GET", f"/api/v2/pages/{page_id}/inline-comments",
        params={"limit": min(max(limit, 1), 50), "body-format": "storage"},
    )
    results = []
    for row in data.get("results", []):
        storage = (row.get("body") or {}).get("storage") or {}
        results.append({"id": row.get("id"), "body": storage.get("value", "")})
    return results


def create_inline_comment(
    page_id: str,
    text_selection: str,
    comment: str,
    match_count: int = 1,
    match_index: int = 0,
) -> dict:
    if not text_selection.strip() or not comment.strip():
        raise ValueError("A selected text and comment are required.")
    safe_comment = escape(comment.strip(), quote=False)
    data = _request(
        "POST", "/api/v2/inline-comments",
        json={
            "pageId": page_id,
            "body": {"representation": "storage", "value": f"<p>{safe_comment}</p>"},
            "inlineCommentProperties": {
                "textSelection": text_selection,
                "textSelectionMatchCount": match_count,
                "textSelectionMatchIndex": match_index,
            },
        },
    )
    return {"id": data.get("id"), "page_id": data.get("pageId"),
            "resolution_status": data.get("resolutionStatus")}


def get_footer_comments(page_id: str, limit: int = 50) -> list[dict]:
    data = _request(
        "GET", f"/api/v2/pages/{page_id}/footer-comments",
        params={"limit": min(max(limit, 1), 50), "body-format": "storage"},
    )
    results = []
    for row in data.get("results", []):
        storage = (row.get("body") or {}).get("storage") or {}
        results.append({"id": row.get("id"), "body": storage.get("value", "")})
    return results


def create_footer_comment(page_id: str, comment: str) -> dict:
    if not comment.strip():
        raise ValueError("A comment is required.")
    data = _request(
        "POST", "/api/v2/footer-comments",
        json={
            "pageId": page_id,
            "body": {"representation": "storage", "value": f"<p>{escape(comment.strip(), quote=False)}</p>"},
        },
    )
    return {"id": data.get("id"), "page_id": data.get("pageId")}


def update_page(page_id: str, title: str, body: str, version: int) -> dict:
    if version < 1:
        raise ValueError("Page version must be positive.")
    data = _request(
        "PUT", f"/api/v2/pages/{page_id}",
        json={
            "id": page_id, "status": "current", "title": title,
            "body": {"representation": "storage", "value": body},
            "version": {"number": version + 1},
        },
    )
    return {"id": data.get("id"), "title": data.get("title"),
            "version": (data.get("version") or {}).get("number")}

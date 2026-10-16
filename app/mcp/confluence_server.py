from mcp.server.mcpserver import MCPServer

from app.integrations.confluence import (
    create_folder, create_footer_comment, create_inline_comment, create_page,
    get_folder, get_folder_children, get_footer_comments, get_inline_comments, get_page, get_spaces,
    search_pages, update_page,
)

mcp = MCPServer("Confluence MCP Server")


@mcp.tool()
def list_confluence_spaces(limit: int = 25) -> dict:
    """List Confluence spaces visible to the configured Atlassian account."""
    return {"status": "success", "spaces": get_spaces(limit)}


@mcp.tool()
def search_confluence_pages(query: str, space_key: str | None = None, limit: int = 10) -> dict:
    """Search visible Confluence pages by text and optionally space key."""
    return {"status": "success", "pages": search_pages(query, space_key, limit)}


@mcp.tool()
def get_confluence_page(page_id: str) -> dict:
    """Read page title, version, hierarchy identifiers, and storage-format body."""
    return {"status": "success", "page": get_page(page_id)}


@mcp.tool()
def create_confluence_page(
    space_id: str, title: str, body: str, parent_id: str | None = None,
) -> dict:
    """Create a Confluence page in a space, optionally under a parent."""
    return {"status": "success", "page": create_page(space_id, title, body, parent_id)}


@mcp.tool()
def create_confluence_folder(
    space_id: str, title: str, parent_id: str | None = None,
) -> dict:
    """Create a Confluence folder in a space, optionally under a parent."""
    return {"status": "success", "folder": create_folder(space_id, title, parent_id)}


@mcp.tool()
def get_confluence_folder(folder_id: str) -> dict:
    """Read a Confluence folder's name, space, parent and version."""
    return {"status": "success", "folder": get_folder(folder_id)}


@mcp.tool()
def get_confluence_folder_children(folder_id: str, limit: int = 25) -> dict:
    """List direct pages and folders inside a Confluence folder."""
    return {"status": "success", "children": get_folder_children(folder_id, limit)}


@mcp.tool()
def list_confluence_inline_comments(page_id: str, limit: int = 50) -> dict:
    """List existing inline comments on a page."""
    return {"status": "success", "comments": get_inline_comments(page_id, limit)}


@mcp.tool()
def add_confluence_inline_comment(
    page_id: str, text_selection: str, comment: str,
) -> dict:
    """Add an inline comment anchored to a unique phrase on a page."""
    return {
        "status": "success",
        "comment": create_inline_comment(page_id, text_selection, comment),
    }


@mcp.tool()
def list_confluence_footer_comments(page_id: str, limit: int = 50) -> dict:
    """List existing page-level comments."""
    return {"status": "success", "comments": get_footer_comments(page_id, limit)}


@mcp.tool()
def add_confluence_footer_comment(page_id: str, comment: str) -> dict:
    """Add a page-level comment for findings that have no exact text anchor."""
    return {"status": "success", "comment": create_footer_comment(page_id, comment)}


@mcp.tool()
def update_confluence_page(page_id: str, title: str, body: str, version: int) -> dict:
    """Replace a page's title and storage-format body using its current version."""
    return {"status": "success", "page": update_page(page_id, title, body, version)}


if __name__ == "__main__":
    mcp.run()

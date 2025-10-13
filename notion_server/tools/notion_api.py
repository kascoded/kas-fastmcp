import httpx
from typing import Optional, Dict, Any, List
from fastmcp import FastMCP
from notion_server.server import mcp 
from config import NotionConfig


# --- Helper for headers ---
def _headers() -> Dict[str, str]:
    if not NotionConfig.TOKEN:
        raise RuntimeError("Missing NOTION_TOKEN")

    return {
        "Authorization": f"Bearer {NotionConfig.TOKEN}",
        "Notion-Version": NotionConfig.API_VERSION,
        "Content-Type": "application/json",
    }


# --- Unified Query Tool ---
@mcp.tool
def notion_query(
    source_name: str = "zettelkasten",
    filter: Optional[Dict[str, Any]] = None,
    sorts: Optional[List[Dict[str, Any]]] = None,
    page_size: Optional[int] = 10,
    start_cursor: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Query a Notion database or data source dynamically.
    - Uses /v1/data_sources/... if a data_source_id exists (2025-09-03+)
    - Falls back to /v1/databases/... for legacy setups
    """
    source = NotionConfig.DATABASES.get(source_name)
    if not source:
        raise ValueError(f"Source '{source_name}' not found in config.")

    # Use new endpoint if data_source_id is defined
    if source["data_source_id"]:
        url = f"https://api.notion.com/v1/data_sources/{source['data_source_id']}/query"
    else:
        url = f"https://api.notion.com/v1/databases/{source['database_id']}/query"

    payload: Dict[str, Any] = {}
    if filter:
        payload["filter"] = filter
    if sorts:
        payload["sorts"] = sorts
    if page_size:
        payload["page_size"] = page_size
    if start_cursor:
        payload["start_cursor"] = start_cursor

    with httpx.Client(timeout=30) as client:
        r = client.post(url, headers=_headers(), json=payload)
        r.raise_for_status()
        return r.json()


# --- Retrieve a Page ---
@mcp.tool
def notion_get_page(page_id: str) -> Dict[str, Any]:
    """Retrieve a Notion page by ID (works for both databases and data sources)."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    with httpx.Client(timeout=30) as client:
        r = client.get(url, headers=_headers())
        r.raise_for_status()
        return r.json()


# --- Create Item Tool ---
@mcp.tool
def notion_create_item(
    source_name: str,
    properties: Dict[str, Any],
    parent_page_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new page/item in a Notion database or data source.
    - Automatically detects whether to use /pages or /data_sources/{id}/items (new API)
    - Compatible with Notion API 2025-09-03
    """
    source = NotionConfig.DATABASES.get(source_name)
    if not source:
        raise ValueError(f"Source '{source_name}' not found in config.")

    if source["data_source_id"]:
        # New data source API (2025-09-03+)
        url = f"https://api.notion.com/v1/data_sources/{source['data_source_id']}/items"
        payload = {"properties": properties}
    else:
        # Legacy database API (pre-2025)
        url = "https://api.notion.com/v1/pages"
        payload = {
            "parent": {"database_id": source["database_id"]},
            "properties": properties,
        }
        if parent_page_id:
            payload["parent"]["page_id"] = parent_page_id

    with httpx.Client(timeout=30) as client:
        r = client.post(url, headers=_headers(), json=payload)
        r.raise_for_status()
        return r.json()

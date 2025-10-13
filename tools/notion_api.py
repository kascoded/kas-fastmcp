import os
import httpx
from typing import Optional, Dict, Any, List
from fastmcp import tool  # import decorator directly if needed

# --- Environment variables ---
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_API_VERSION = os.getenv("NOTION_API_VERSION", "2022-06-28")
DEFAULT_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
DEFAULT_DATA_SOURCE_ID = os.getenv("NOTION_DATA_SOURCE_ID")

# --- Helper for headers ---
def _headers() -> Dict[str, str]:
    if not NOTION_TOKEN:
        raise RuntimeError("Missing NOTION_TOKEN")
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
    }

# --- Tools ---
@tool
def notion_query_database(
    database_id: Optional[str] = None,
    filter: Optional[Dict[str, Any]] = None,
    sorts: Optional[List[Dict[str, Any]]] = None,
    page_size: Optional[int] = 10,
    start_cursor: Optional[str] = None,
) -> Dict[str, Any]:
    """Query a Notion database (API 2022-06-28)."""
    did = database_id or DEFAULT_DATABASE_ID
    if not did:
        raise ValueError("database_id is required (or set NOTION_DATABASE_ID)")
    url = f"https://api.notion.com/v1/databases/{did}/query"
    payload: Dict[str, Any] = {}
    if filter: payload["filter"] = filter
    if sorts: payload["sorts"] = sorts
    if page_size: payload["page_size"] = page_size
    if start_cursor: payload["start_cursor"] = start_cursor
    with httpx.Client(timeout=30) as client:
        r = client.post(url, headers=_headers(), json=payload)
    r.raise_for_status()
    return r.json()


@tool
def notion_query_data_source(
    data_source_id: Optional[str] = None,
    filter: Optional[Dict[str, Any]] = None,
    sorts: Optional[List[Dict[str, Any]]] = None,
    page_size: Optional[int] = 10,
    start_cursor: Optional[str] = None,
) -> Dict[str, Any]:
    """Query a Notion data source (API 2025-09-03)."""
    dsid = data_source_id or DEFAULT_DATA_SOURCE_ID
    if not dsid:
        raise ValueError("data_source_id is required (or set NOTION_DATA_SOURCE_ID)")
    url = f"https://api.notion.com/v1/data_sources/{dsid}/query"
    payload: Dict[str, Any] = {}
    if filter: payload["filter"] = filter
    if sorts: payload["sorts"] = sorts
    if page_size: payload["page_size"] = page_size
    if start_cursor: payload["start_cursor"] = start_cursor
    with httpx.Client(timeout=30) as client:
        r = client.post(url, headers=_headers(), json=payload)
    r.raise_for_status()
    return r.json()


@tool
def notion_get_page(page_id: str) -> Dict[str, Any]:
    """Retrieve a Notion page by ID."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    with httpx.Client(timeout=30) as client:
        r = client.get(url, headers=_headers())
    r.raise_for_status()
    return r.json()

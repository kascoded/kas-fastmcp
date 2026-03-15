"""
Notion Query Tools
Search, query, and discovery operations for Notion databases and pages.
"""

from typing import Optional, Dict, Any, List
from notion_server.server import mcp
from notion_server.deps import _client, _schema_manager, _property_formatter
from config import NotionConfig


@mcp.tool
async def notion_query(
    source_name: str,
    filter: Optional[Dict[str, Any]] = None,
    sorts: Optional[List[Dict[str, Any]]] = None,
    page_size: int = 10,
    start_cursor: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Query pages from a data source (preferred for 2025-09-03).
    Falls back: if only database_id provided, resolves its data_source_id first.
    
    Args:
        source_name: Name of the data source from config
        filter: Notion filter object
        sorts: List of sort objects
        page_size: Number of results (1-100)
        start_cursor: Pagination cursor
    
    Returns:
        Full Notion API response with results array
    """
    data_source_id = await _schema_manager.get_data_source_id(source_name)

    payload = {
        k: v
        for k, v in {
            "filter": filter,
            "sorts": sorts,
            "page_size": page_size,
            "start_cursor": start_cursor,
        }.items()
        if v is not None
    }
    
    return await _client.post(f"data_sources/{data_source_id}/query", payload)


@mcp.tool
async def notion_find_page_by_name(
    source_name: str,
    page_name: str,
    title_property: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Find the first page whose title property equals `page_name`.

    Args:
        source_name: Name of the data source from config
        page_name: Exact title to search for
        title_property: Name of the title property — defaults to the value configured
                        for this database in databases.yaml (usually "title")

    Returns:
        Compact object with page_id, title, properties, last_edited, and URL
        If not found, returns {"found": False}
    """
    data_source_id = await _schema_manager.get_data_source_id(source_name)
    if title_property is None:
        title_property = NotionConfig.get_title_property(source_name)

    payload = {
        "filter": {
            "property": title_property,
            "title": {"equals": page_name},
        },
        "page_size": 1,
    }
    
    result = await _client.post(f"data_sources/{data_source_id}/query", payload)
    results = result.get("results", [])
    
    if not results:
        return {
            "found": False, 
            "message": f"No page named '{page_name}' in '{source_name}'."
        }

    page = results[0]
    page_id = page.get("id")
    props = page.get("properties", {})

    return {
        "found": True,
        "page_id": page_id,
        "title": _property_formatter.extract_title(props),
        "properties": _property_formatter.format_for_display(props),
        "last_edited": page.get("last_edited_time"),
        "url": f"https://www.notion.so/{(page_id or '').replace('-', '')}",
    }


@mcp.tool
async def notion_search(
    query: Optional[str] = None,
    filter: Optional[Dict[str, Any]] = None,
    sort: Optional[Dict[str, Any]] = None,
    page_size: int = 10,
    start_cursor: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Workspace search (pages, databases, etc.).
    Useful to discover page IDs by title.
    
    Args:
        query: Text to search for
        filter: Filter by object type (e.g., {"property": "object", "value": "page"})
        sort: Sort configuration
        page_size: Number of results (1-100)
        start_cursor: Pagination cursor
    
    Returns:
        Search results with matching pages/databases
    """
    payload = {
        k: v
        for k, v in {
            "query": query,
            "filter": filter,
            "sort": sort,
            "page_size": page_size,
            "start_cursor": start_cursor,
        }.items()
        if v is not None
    }
    
    return await _client.post("search", payload)


@mcp.tool
async def notion_list_data_sources(source_name: str) -> Dict[str, Any]:
    """
    List all data sources for a database.
    Useful when a database has multiple data sources.
    
    Args:
        source_name: Name from config that has a database_id
    
    Returns:
        List of data sources under this database with IDs and names
    """
    source_config = _schema_manager.get_source_config(source_name)
    db_id = source_config.get("database_id")
    
    if not db_id:
        raise ValueError(f"Source '{source_name}' doesn't have a database_id configured.")
    
    db_json = await _client.get(f"databases/{db_id}")
    data_sources = db_json.get("data_sources", [])
    
    return {
        "database_id": db_id,
        "data_sources": [
            {
                "id": ds.get("id"),
                "name": ds.get("name"),
            }
            for ds in data_sources
        ],
        "count": len(data_sources),
    }

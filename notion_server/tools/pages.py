"""
Notion Page Tools
CRUD operations for Notion pages and their properties.
"""

from typing import Optional, Dict, Any
from notion_server.server import mcp
from notion_server.core import NotionClient, SchemaManager, PropertyFormatter, BlockFormatter
from notion_server.utils import PropertyValidator


# Initialize core modules
_client = NotionClient()
_schema_manager = SchemaManager(_client)
_property_formatter = PropertyFormatter()
_block_formatter = BlockFormatter()


@mcp.tool
async def notion_get_page(page_id: str, include_content: bool = False) -> Dict[str, Any]:
    """
    Retrieve a single page by ID.
    
    Args:
        page_id: The page ID
        include_content: If True, also fetches and includes page content as markdown
    
    Returns:
        Page object with properties, optionally with content
    """
    page = await _client.get(f"pages/{page_id}")
    
    result = {
        "id": page.get("id"),
        "title": _property_formatter.extract_title(page.get("properties", {})),
        "properties": _property_formatter.format_for_display(page.get("properties", {})),
        "url": page.get("url"),
        "created_time": page.get("created_time"),
        "last_edited_time": page.get("last_edited_time"),
        "archived": page.get("archived"),
    }
    
    if include_content:
        blocks_result = await _client.get(f"blocks/{page_id}/children")
        blocks = blocks_result.get("results", [])
        result["content_markdown"] = _block_formatter.to_markdown(blocks)
    
    return result


@mcp.tool
async def notion_get_data_source(source_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a data source including its schema/properties.
    
    Args:
        source_name: Name of the data source from config (e.g., 'zettelkasten')
    
    Returns:
        Data source details including properties schema with types and options
    """
    schema = await _schema_manager.get_schema(source_name)
    data_source_id = await _schema_manager.get_data_source_id(source_name)
    
    result = await _client.get(f"data_sources/{data_source_id}")
    
    title_array = result.get("title", [])
    title = title_array[0].get("plain_text", "Untitled") if title_array else "Untitled"
    
    desc_array = result.get("description", [])
    description = desc_array[0].get("plain_text", "") if desc_array else ""
    
    return {
        "data_source_id": result.get("id"),
        "title": title,
        "description": description,
        "properties": schema,
        "url": result.get("url"),
    }


@mcp.tool
async def notion_create_item(
    source_name: str,
    properties: Dict[str, Any],
    content_markdown: Optional[str] = None,
    parent_page_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new page.
    In API 2025-09-03, pages are parented by a data source (preferred) or by another page.
    Properties are validated against the database schema before creation.
    
    Args:
        source_name: Name of the data source from config
        properties: Page properties (must include title property)
        content_markdown: Optional markdown content to add to the page
        parent_page_id: Optional parent page ID (otherwise uses data source)
    
    Returns:
        Created page object with page_id, title, url, and created_time
    """
    import sys
    print(f"[DEBUG] notion_create_item called with source={source_name}", file=sys.stderr, flush=True)
    # Validate properties against schema
    import sys
    print(f"[VALIDATION] Starting validation for source: {source_name}", file=sys.stderr)
    print(f"[VALIDATION] Properties to validate: {list(properties.keys())}", file=sys.stderr)
    
    try:
        schema = await _schema_manager.get_schema(source_name)
        print(f"[VALIDATION] Schema fetched, has {len(schema)} properties", file=sys.stderr)
        
        validator = PropertyValidator(schema)
        is_valid, errors = validator.validate_properties(properties)
        
        print(f"[VALIDATION] Validation result: valid={is_valid}, errors={len(errors)}", file=sys.stderr)
        
        if not is_valid:
            print(f"[VALIDATION] Raising validation error", file=sys.stderr)
            raise ValueError(
                f"Property validation failed:\n" +
                "\n".join(f"  • {error}" for error in errors)
            )
    except ValueError:
        # Re-raise validation errors
        print(f"[VALIDATION] Re-raising ValueError", file=sys.stderr)
        raise
    except Exception as e:
        # Log schema fetch errors but continue (don't block creation)
        print(f"Warning: Schema validation skipped due to error: {e}", file=sys.stderr)
    
    payload: Dict[str, Any] = {
        "properties": properties or {},
    }

    if parent_page_id:
        payload["parent"] = {"page_id": parent_page_id}
    else:
        data_source_id = await _schema_manager.get_data_source_id(source_name)
        payload["parent"] = {"data_source_id": data_source_id}

    # Add content if provided
    if content_markdown:
        payload["children"] = _block_formatter.from_markdown(content_markdown)

    result = await _client.post("pages", payload)
    
    return {
        "page_id": result.get("id"),
        "title": _property_formatter.extract_title(result.get("properties", {})),
        "url": result.get("url"),
        "created_time": result.get("created_time"),
    }


@mcp.tool
async def notion_update_item(
    page_id: str,
    properties: Optional[Dict[str, Any]] = None,
    archived: Optional[bool] = None,
    icon: Optional[Dict[str, Any]] = None,
    cover: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Update an existing page's properties (and optionally archived/icon/cover).
    Note: For property validation, you must fetch the page first to determine its source.
    
    Args:
        page_id: The page ID to update
        properties: Properties to update (partial update supported)
        archived: Archive or restore the page
        icon: Update page icon
        cover: Update page cover
    
    Returns:
        Updated page object with page_id, title, url, and confirmation
    """
    payload: Dict[str, Any] = {}
    
    if properties:
        payload["properties"] = properties
    if archived is not None:
        payload["archived"] = archived
    if icon is not None:
        payload["icon"] = icon
    if cover is not None:
        payload["cover"] = cover

    result = await _client.patch(f"pages/{page_id}", payload)
    
    return {
        "page_id": result.get("id"),
        "title": _property_formatter.extract_title(result.get("properties", {})),
        "url": result.get("url"),
        "updated": True,
    }

"""
Notion Content Tools
Operations for reading and writing page content (blocks).
"""

from typing import Dict, Any
from notion_server.server import mcp
from notion_server.core import NotionClient, PropertyFormatter, BlockFormatter


# Initialize core modules
_client = NotionClient()
_property_formatter = PropertyFormatter()
_block_formatter = BlockFormatter()


@mcp.tool
async def notion_get_page_content(page_id: str) -> Dict[str, Any]:
    """
    Get the content of a page as markdown.
    Useful for reading notes, documentation, etc.
    
    Args:
        page_id: The page ID to read content from
    
    Returns:
        Object with page_id, title, content in markdown format, and URL
    """
    page = await _client.get(f"pages/{page_id}")
    blocks_result = await _client.get(f"blocks/{page_id}/children")
    blocks = blocks_result.get("results", [])
    
    return {
        "page_id": page_id,
        "title": _property_formatter.extract_title(page.get("properties", {})),
        "content_markdown": _block_formatter.to_markdown(blocks),
        "url": page.get("url"),
    }


@mcp.tool
async def notion_append_content(
    page_id: str,
    content_markdown: str,
) -> Dict[str, Any]:
    """
    Append content blocks to an existing page.
    Useful for adding notes, updates, or new sections.
    
    Args:
        page_id: The page to append to
        content_markdown: Markdown content to append (supports headings, lists, paragraphs, etc.)
    
    Returns:
        Confirmation with page_id, number of blocks added, and URL
    """
    blocks = _block_formatter.from_markdown(content_markdown)
    payload = {"children": blocks}
    
    await _client.patch(f"blocks/{page_id}/children", payload)
    
    return {
        "page_id": page_id,
        "appended": True,
        "blocks_added": len(blocks),
        "url": f"https://www.notion.so/{page_id.replace('-', '')}",
    }

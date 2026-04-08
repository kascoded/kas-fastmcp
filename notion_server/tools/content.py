"""
Notion Content Tools
Operations for reading and writing page content (blocks).
"""

import asyncio
import logging
import time
from typing import Dict, Any
from notion_server.server import mcp
from notion_server.deps import _client, _property_formatter, _block_formatter

logger = logging.getLogger(__name__)

_MAX_BLOCK_PAGES = 100  # Maximum pagination iterations (~10 000 blocks at page_size=100)
_BLOCK_FETCH_TOTAL_TIMEOUT = 120  # seconds — hard wall-clock cap across all pages


async def _get_all_blocks(page_id: str) -> list:
    """Fetch all block children, following pagination cursors.

    Caps at _MAX_BLOCK_PAGES iterations and _BLOCK_FETCH_TOTAL_TIMEOUT seconds
    to prevent runaway fetches on extremely large pages.
    Passes the pagination cursor as a proper query parameter rather than
    appending it to the URL string.
    """
    blocks = []
    endpoint = f"blocks/{page_id}/children"
    params = None
    iterations = 0
    start_time = time.monotonic()

    while True:
        if iterations >= _MAX_BLOCK_PAGES:
            logger.warning(
                "blocks/%s/children: reached %d-page iteration cap; "
                "returning %d blocks fetched so far",
                page_id,
                _MAX_BLOCK_PAGES,
                len(blocks),
            )
            break

        elapsed = time.monotonic() - start_time
        if elapsed >= _BLOCK_FETCH_TOTAL_TIMEOUT:
            logger.warning(
                "blocks/%s/children: total timeout of %ds exceeded after %d iterations; "
                "returning %d blocks fetched so far",
                page_id,
                _BLOCK_FETCH_TOTAL_TIMEOUT,
                iterations,
                len(blocks),
            )
            break

        result = await _client.get(endpoint, params=params)
        blocks.extend(result.get("results", []))
        iterations += 1

        if not result.get("has_more"):
            break

        cursor = result.get("next_cursor")
        if not cursor:
            logger.warning(
                "blocks/%s/children: has_more=True but next_cursor is None "
                "after %d iterations; stopping to avoid infinite loop",
                page_id,
                iterations,
            )
            break

        params = {"start_cursor": cursor}

    return blocks


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
    blocks = await _get_all_blocks(page_id)

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


@mcp.tool
async def notion_replace_content(
    page_id: str,
    content_markdown: str,
) -> Dict[str, Any]:
    """
    Replace ALL content blocks on a page with new markdown content.
    This works by fetching all existing block IDs, deleting them, and then appending new ones.
    
    Args:
        page_id: The page to update
        content_markdown: New markdown content
    
    Returns:
        Confirmation with page_id and number of new blocks added
    """
    # 1. Get all existing blocks
    existing_blocks = await _get_all_blocks(page_id)
    
    # 2. Delete all existing blocks in parallel (each must be deleted individually per Notion API)
    block_ids = [block["id"] for block in existing_blocks if block.get("id")]
    if block_ids:
        await asyncio.gather(*[_client.delete(f"blocks/{bid}") for bid in block_ids])
            
    # 3. Append new blocks
    blocks = _block_formatter.from_markdown(content_markdown)
    if blocks:
        payload = {"children": blocks}
        await _client.patch(f"blocks/{page_id}/children", payload)
    
    return {
        "page_id": page_id,
        "replaced": True,
        "blocks_deleted": len(existing_blocks),
        "blocks_added": len(blocks),
        "url": f"https://www.notion.so/{page_id.replace('-', '')}",
    }

"""
Shared dependency instances for Notion MCP tools.
A single NotionClient and SchemaManager are shared across all tool modules
to avoid redundant schema caches and connection pool fragmentation.
Formatter instances are stateless (all static methods) but kept here so
tool modules don't each instantiate their own copies.
"""
import atexit
import asyncio
from notion_server.core import NotionClient, SchemaManager, PropertyFormatter, BlockFormatter

_client = NotionClient()
_schema_manager = SchemaManager(_client)
_property_formatter = PropertyFormatter()
_block_formatter = BlockFormatter()


def _sync_close():
    """Close the shared HTTP client on interpreter exit.

    Uses a fresh event loop so this is safe regardless of whether the
    FastMCP server's event loop is still running or has already been closed.
    """
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_client.close())
    except Exception:
        pass
    finally:
        loop.close()


atexit.register(_sync_close)

"""
Shared dependency instances for Notion MCP tools.
A single NotionClient and SchemaManager are shared across all tool modules
to avoid redundant schema caches and connection pool fragmentation.
Formatter instances are stateless (all static methods) but kept here so
tool modules don't each instantiate their own copies.

Note: The shared httpx.AsyncClient inside _client is closed via the FastMCP
lifespan hook in server.py (`await _client.close()` on shutdown).
"""
from notion_server.core import NotionClient, SchemaManager, PropertyFormatter, BlockFormatter

_client = NotionClient()
_schema_manager = SchemaManager(_client)
_property_formatter = PropertyFormatter()
_block_formatter = BlockFormatter()

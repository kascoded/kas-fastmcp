"""
Shared dependency instances for Notion MCP tools.
A single NotionClient and SchemaManager are shared across all tool modules
to avoid redundant schema caches and connection pool fragmentation.
Formatter instances are stateless (all static methods) but kept here so
tool modules don't each instantiate their own copies.

Note: The shared httpx.AsyncClient inside _client is intentionally not closed
via atexit. Spinning up a new event loop inside an atexit handler is fragile
(the server loop may already be closed) and the OS reclaims file descriptors on
process exit anyway. If FastMCP adds a lifespan hook in a future release, wire
`await _client.close()` there instead.
"""
from notion_server.core import NotionClient, SchemaManager, PropertyFormatter, BlockFormatter

_client = NotionClient()
_schema_manager = SchemaManager(_client)
_property_formatter = PropertyFormatter()
_block_formatter = BlockFormatter()

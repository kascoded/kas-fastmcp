"""
Shared dependency instances for Notion MCP tools.
A single NotionClient and SchemaManager are shared across all tool modules
to avoid redundant schema caches and connection pool fragmentation.
Formatter instances are stateless (all static methods) but kept here so
tool modules don't each instantiate their own copies.
"""
from notion_server.core import NotionClient, SchemaManager, PropertyFormatter, BlockFormatter

_client = NotionClient()
_schema_manager = SchemaManager(_client)
_property_formatter = PropertyFormatter()
_block_formatter = BlockFormatter()

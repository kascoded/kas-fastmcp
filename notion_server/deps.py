"""
Shared dependency instances for Notion MCP tools.
A single NotionClient and SchemaManager are shared across all tool modules
to avoid redundant schema caches and connection pool fragmentation.
"""
from notion_server.core import NotionClient, SchemaManager

_client = NotionClient()
_schema_manager = SchemaManager(_client)

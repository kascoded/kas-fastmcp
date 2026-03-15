"""
Notion MCP Resources
Exposes Notion configuration and schema data as MCP resources so agents can
read them without consuming tool call budget.

Resources:
  notion://databases                          — list of all configured databases
  notion://databases/{source_name}/schema     — property schema for one database
"""

import json
from notion_server.server import mcp
from notion_server.deps import _schema_manager
from config import NotionConfig


@mcp.resource(
    "notion://databases",
    name="notion_databases",
    description=(
        "List of all Notion databases configured in this server. "
        "Returns source names, descriptions, and title property names. "
        "Read this first to discover available databases before querying or creating items."
    ),
    mime_type="application/json",
)
def list_databases() -> str:
    """Return all configured database names and their metadata from config."""
    databases = {}
    for source_name in NotionConfig.list_databases():
        config = NotionConfig.get_database_config(source_name)
        databases[source_name] = {
            "description": config.get("description", ""),
            "title_property": config.get("title_property", "title"),
            "has_database_id": bool(config.get("database_id")),
            "has_data_source_id": bool(config.get("data_source_id")),
            "has_schema_cached": NotionConfig.has_schema(source_name),
        }
    return json.dumps({"databases": databases, "count": len(databases)}, indent=2)


@mcp.resource(
    "notion://databases/{source_name}/schema",
    name="notion_database_schema",
    description=(
        "Property schema for a specific Notion database. "
        "Returns all property names, types, and available options (for select/multi-select). "
        "Read this before calling notion_create_item or notion_update_item to know "
        "which properties exist and what values are valid."
    ),
    mime_type="application/json",
)
async def get_database_schema(source_name: str) -> str:
    """Fetch and return the schema for the named database via SchemaManager (cached, 1h TTL)."""
    schema = await _schema_manager.get_schema(source_name)
    title_property = NotionConfig.get_title_property(source_name)
    return json.dumps({
        "source_name": source_name,
        "title_property": title_property,
        "properties": schema,
        "property_count": len(schema),
    }, indent=2)

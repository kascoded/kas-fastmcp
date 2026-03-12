# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A FastMCP server that exposes Notion database operations as MCP tools. It uses Notion API version `2025-09-03` which introduces the `data_sources` concept (querying uses `/data_sources/{id}/query` rather than `/databases/{id}/query`).

## Commands

```bash
# Run the server
python main.py
fastmcp run main.py

# Lint
ruff check .
black --check .

# Connection tests (require .env and databases.yaml configured)
python tools/connection_testing/token_verification.py
python tools/connection_testing/test_connection.py
```

Tests are run with pytest but there are no automated tests currently — only manual connection testing scripts.

## Architecture

**Dependency flow** (no circular imports):
```
main.py → config.py
main.py → notion_server/server.py → notion_server/tools/* → notion_server/core/* → config.py
```

**Key layers:**
- `config.py` — `NotionConfig` class, loads from `databases.yaml` (local) or env vars (cloud). YAML takes priority.
- `notion_server/server.py` — Creates the `FastMCP("KasNotionMCP")` instance as `mcp`/`server`, then imports tools to register them via `@mcp.tool`.
- `notion_server/core/` — Pure business logic, no MCP dependencies:
  - `client.py` — `NotionClient`: async httpx wrapper for Notion API
  - `schema.py` — `SchemaManager`: fetches/caches database schemas and resolves `data_source_id`
  - `formatters.py` — `PropertyFormatter`, `BlockFormatter`: Notion ↔ markdown/display conversions
- `notion_server/deps.py` — Single shared `NotionClient` + `SchemaManager` instances imported by all tool modules
- `notion_server/tools/` — Thin `@mcp.tool` wrappers (import shared instances from `deps.py`):
  - `query.py` — search/discovery operations
  - `pages.py` — CRUD + schema validation via `PropertyValidator`
  - `content.py` — block read/write (markdown), paginates all block children automatically
  - `schema_sync.py` — sync schemas from Notion, discover databases, validate config
- `notion_server/utils/validators.py` — `PropertyValidator`: validates properties against fetched schemas before API calls

## Configuration

**`databases.yaml`** (committed, required for local and cloud):
```yaml
zettelkasten:
  data_source_id: "..."
  database_id: "..."
  title_property: "title"
  description: "..."
```

**`.env`** (not committed):
```
NOTION_TOKEN=ntn_...
NOTION_API_VERSION=2025-09-03
```

For cloud deployments without `databases.yaml`, use env vars like `ZETTELKASTEN_DATA_SOURCE_ID`, `ZETTELKASTEN_DATABASE_ID`, etc.

## Important API Notes

- Notion API `2025-09-03` uses `data_sources` — query via `POST /data_sources/{id}/query`, not `POST /databases/{id}/query`
- `SchemaManager.get_data_source_id()` will auto-resolve from `database_id` via API if `data_source_id` is not in config, and caches the result in memory
- Schema is fetched from `GET /data_sources/{id}` and cached with a 1-hour TTL; full API response is also cached for metadata access via `SchemaManager.get_data_source_info()`
- `notion_create_item` validates properties against the schema before calling the API; validation errors fail loudly. Schema fetch errors are swallowed (creation proceeds).
- `notion_update_item` accepts an optional `source_name` parameter — when provided, properties are validated before the PATCH call.

## Adding a New Tool

1. Choose `query.py`, `pages.py`, `content.py`, or `schema_sync.py`
2. Import `mcp` from `notion_server.server`
3. Import `_client` and/or `_schema_manager` from `notion_server.deps` (do NOT instantiate new ones)
4. Decorate with `@mcp.tool`

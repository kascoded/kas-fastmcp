# Changelog

All notable changes to kas-fastmcp.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.3.1] - 2026-04-10

### Fixed

- **`notion_discover_databases` broken — wrong search filter value** — The `filter.value` was set to `"database"`, which is not a valid value in Notion API `2025-09-03+`. Changed to `"data_source"` (the only valid options are `"page"` and `"data_source"`). The result parsing was also updated: in `data_source` search results, the `id` field is the `data_source_id` directly, and the `database_id` is nested under `database_parent.database_id` — both were previously extracted from the wrong locations.
- **`notion_replace_content` silently ignored block delete failures** — `asyncio.gather` was firing all block deletes with no error handling. Failures are now detected via `return_exceptions=True` and raised with a clear message indicating how many blocks failed and which error occurred first. This prevents partial page corruption where only some blocks are deleted before new content is appended.
- **Schema cache defensive access** — `get_schema()` used `source_name in self._schema_cache` followed by direct `self._schema_cache[source_name]`, which could raise a `KeyError` if another coroutine evicted the entry between the two operations. Both the fast path and the locked path now use `.get()` with a `None` check.

---

## [2.3.0] - 2026-04-02

### Added

- **Persistent Disk-Based Schema Caching** — Implemented a local JSON cache at `~/.cache/kas-fastmcp/schema_cache.json`. Database schemas and data source IDs are now persisted across server restarts, significantly reducing cold-start latency and minimizing Notion API calls.
- **`notion_replace_content` tool** — New tool that clears all existing blocks on a page and appends new Markdown content, enabling "overwrite" functionality for dynamic pages.
- **`is_default` database flag** — Added support for marking a database as the default in `databases.yaml`. This flag is now exposed via the `notion://databases` resource to assist AI agents in selecting the primary workspace.

### Fixed

- **Automatic 429 Rate-Limit Retries** — Updated `NotionClient` to automatically catch `429 Too Many Requests` errors and retry using exponential backoff (respecting the `Retry-After` header when present).
- **Graceful Shutdown Loop** — Replaced `asyncio.run()` in the `atexit` handler with `asyncio.new_event_loop()` to ensure a fresh, safe event loop is available during shutdown regardless of the previous loop's state.

---

## [2.2.0] - 2026-03-14

### Fixed

- **`NotionClient` shared httpx connection pool** — Previously created a new `httpx.AsyncClient` per request; now a single client is created in `__init__` and reused across all requests for proper connection pooling.
- **Code fence parsing in `BlockFormatter.from_markdown`** — Fenced code blocks were not parsed and fell through as plain paragraphs. Now detected with a state machine (`in_code` flag), preserving indentation and mapping the language tag. Unterminated fences are flushed at EOF.
- **Async double-checked locking in `SchemaManager`** — `get_schema()` and `get_data_source_id()` now use `asyncio.Lock` with double-checked locking to prevent redundant concurrent fetches.
- **`notion_find_page_by_name` uses configured `title_property`** — Was hardcoded to `"title"`; now reads `NotionConfig.get_title_property(source_name)`.
- **`notion_discover_databases` filter corrected** — Search filter was broken (empty results). Now uses `{"property": "object", "value": "database"}` correctly.
- **`notion_get_page(include_content=True)` fully paginated** — Now calls `_get_all_blocks()` (imported from `content.py`) instead of a single non-paginated block fetch.
- **`reading_list` database removed** — Removed from `databases.yaml` (database does not exist). Database count is now 12.

### Added

- **`NotionClient.close()`** — `async def close()` calls `self._http.aclose()` for graceful shutdown in tests and direct lifecycle management.
- **MCP resource endpoints** — New `notion_server/tools/resources.py` registers two resources:
  - `notion://databases` — lists all configured databases as JSON
  - `notion://databases/{source_name}/schema` — returns the cached schema for a specific database

---

## [2.1.0] - 2026-03-12

### Fixed

- **Infinite loop in block pagination** — `_get_all_blocks` was not passing the `next_cursor` as a query parameter; it was appended to the URL string, so Notion ignored it and returned the first page on every iteration. The cursor is now sent via `params={"start_cursor": cursor}`. Adds a 100-page cap (`_MAX_BLOCK_PAGES`) to prevent unbounded loops if the API behaves unexpectedly.
- **`NotionClient.get()` missing `params` support** — `get()` and the underlying `request()` method had no way to pass query string parameters. Both now accept an optional `params` dict forwarded to `httpx`.
- **`notion_sync_schemas` overwrote the committed `databases.yaml`** — Schema sync with `update_config=True` now writes to `~/.config/kas-fastmcp/databases.yaml` instead of the project-local file. The project-local `databases.yaml` is preserved as a clean development default and is never overwritten at runtime.
- **`_load_databases_from_yaml` load order** — Config now checks `~/.config/kas-fastmcp/databases.yaml` first (runtime writes) and falls back to the project-local file, matching the new write location.
- **Debug `print` statements removed from `pages.py`** — Multiple `[DEBUG]` and `[VALIDATION]` `sys.stderr` prints left from development have been removed.
- **`notion_update_item` missing schema validation** — The update tool now accepts an optional `source_name` parameter; when provided, properties are validated against the database schema before the PATCH call.
- **`notion_list_databases` removed** — The `notion_list_databases` tool (which searched for `data_source` objects via the search endpoint) was removed because it does not work correctly with Notion API `2025-09-03`. Use `notion_list_data_sources` or `notion_discover_databases` instead.
- **Schema TTL added** — `SchemaManager` previously cached schemas indefinitely. A 1-hour TTL is now enforced; stale entries are re-fetched automatically.
- **`SchemaManager` shared across tool modules** — All tool modules (`query.py`, `pages.py`, `content.py`, `schema_sync.py`) previously instantiated their own `NotionClient` and `SchemaManager`. They now import shared singletons from `notion_server/deps.py`, eliminating redundant schema caches and connection pool fragmentation.
- **`notion_get_data_source` double-fetches eliminated** — The tool previously fetched the raw data source response and then called `get_schema()` which fetched it again. It now uses `SchemaManager.get_data_source_info()` which returns the raw response from the schema cache.

### Added

- **`notion_server/deps.py`** — Single shared `NotionClient` and `SchemaManager` instances for all tool modules.
- **`SchemaManager.get_data_source_info()`** — Returns the full raw `data_source` API response, populated as a side effect of `get_schema()`. Avoids a redundant API call in `notion_get_data_source`.
- **`notion_update_item` `source_name` parameter** — Optional parameter enabling pre-validation of update properties against the database schema.
- **`CLAUDE.md`** — Guidance file for Claude Code covering architecture, key patterns, and conventions for this repository.
- **Atomic write for `databases.yaml`** — Schema sync writes to a sibling `.yaml.tmp` file and then renames it into place, preventing partial writes from corrupting config.

### Changed

- `notion_sync_schemas` logs a warning when called with `update_config=True` so the write destination is always visible in server logs.
- Schema fetch errors in `notion_create_item` are now silently swallowed (creation proceeds) rather than printed to stderr; validation errors still raise loudly.
- `notion_find_page_by_name` `title_property` default corrected from `"Name"` to `"title"` to match the standard Notion default and `databases.yaml` convention.

---

## [2.0.0] - 2026-02-01

Initial production-ready release. Key characteristics:

- FastMCP server exposing Notion operations as MCP tools via Notion API `2025-09-03`
- Modular architecture: `core/` (pure business logic) → `tools/` (MCP wrappers) → `utils/` (validators)
- Schema-first property validation via `PropertyValidator` before every `create` call
- `databases.yaml` for database configuration; env-var fallback for cloud deployments
- Tools: `notion_query`, `notion_find_page_by_name`, `notion_search`, `notion_list_data_sources`, `notion_discover_databases`, `notion_get_page`, `notion_get_data_source`, `notion_create_item`, `notion_update_item`, `notion_get_page_content`, `notion_append_content`, `notion_sync_schemas`, `notion_validate_config`

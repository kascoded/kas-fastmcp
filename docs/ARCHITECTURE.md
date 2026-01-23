# Architecture Documentation

## Overview

This MCP server follows a **layered architecture** with clear separation of concerns and zero circular dependencies.

## Layers

```
┌─────────────────────────────────────┐
│         MCP Protocol Layer          │  ← FastMCP handles this
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│          Tools Layer                │  ← tools/*.py
│  (Query, Pages, Content)            │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│         Core Logic Layer            │  ← core/*.py
│  (Client, Schema, Formatters)      │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│      Notion API (HTTP/REST)         │
└─────────────────────────────────────┘
```

## Design Decisions

### 1. Separation of Concerns

**Why:** Testability, maintainability, reusability

**How:**
- **Core modules** contain pure business logic
- **Tools** are thin wrappers that handle MCP concerns
- **Utils** provide shared functionality

**Benefits:**
- Core modules can be tested without MCP
- Core modules can be reused in other projects
- Changes to MCP don't affect core logic

### 2. No Circular Dependencies

**Why:** Prevents import issues, makes codebase easier to understand

**Dependency Flow:**
```
config.py (standalone)
    ↓
core/client.py → uses config
    ↓
core/schema.py → uses client
core/formatters.py → standalone
    ↓
utils/validators.py → uses schema types
    ↓
tools/*.py → use core modules
    ↓
server.py → registers tools
```

### 3. Immutable Configuration

**Why:** Prevents bugs from runtime config changes

**How:**
- `NotionConfig.DATABASES` is loaded once at startup
- `SchemaManager` caches in memory, never mutates config
- All helper methods return copies, not references

**Example:**
```python
# ❌ BAD (old code)
source["data_source_id"] = fetched_id  # Mutates config!

# ✅ GOOD (new code)
self._data_source_cache[source_name] = fetched_id  # Separate cache
```

### 4. Schema-First Validation

**Why:** Catch errors early, provide better error messages

**How:**
- Fetch schema from Notion API
- Cache for performance
- Validate before API calls

**Benefits:**
- Better error messages
- Prevent invalid API calls
- Type safety

## Module Breakdown

### `config.py`

**Purpose:** Configuration management

**Responsibilities:**
- Load environment variables
- Load databases from YAML
- Validate configuration
- Provide helper methods

**Key Classes:**
- `NotionConfig` - Main configuration class

**Notes:**
- No dependencies on other project modules
- Can be imported anywhere safely

### `core/client.py`

**Purpose:** HTTP communication with Notion API

**Responsibilities:**
- Handle HTTP requests/responses
- Manage headers and authentication
- Provide helpful error messages

**Key Classes:**
- `NotionClient` - Async HTTP wrapper

**Notes:**
- No business logic
- Pure HTTP operations
- Depends only on `config`

### `core/schema.py`

**Purpose:** Schema fetching and management

**Responsibilities:**
- Fetch schemas from Notion API
- Cache schemas in memory
- Resolve data source IDs
- Provide schema helper methods

**Key Classes:**
- `SchemaManager` - Schema operations

**Notes:**
- Uses `NotionClient` for API calls
- Caches to avoid repeated API calls
- Never mutates `NotionConfig`

### `core/formatters.py`

**Purpose:** Format conversion

**Responsibilities:**
- Extract titles from properties
- Format properties for display
- Convert markdown ↔ Notion blocks

**Key Classes:**
- `PropertyFormatter` - Property formatting
- `BlockFormatter` - Block/markdown conversion

**Notes:**
- Standalone (no external dependencies)
- Pure functions (no side effects)
- Easy to test

### `utils/validators.py`

**Purpose:** Property validation

**Responsibilities:**
- Validate properties against schema
- Check property types
- Validate select options
- Detect read-only properties

**Key Classes:**
- `PropertyValidator` - Validation logic

**Notes:**
- Works with schema from `SchemaManager`
- Returns validation results (doesn't throw)
- Helper function `quick_validate()` for convenience

### `tools/query.py`

**Purpose:** Search and discovery operations

**Tools:**
- `notion_query` - Query database
- `notion_find_page_by_name` - Find by title
- `notion_search` - Workspace search
- `notion_list_databases` - List databases
- `notion_list_data_sources` - List data sources

**Notes:**
- Uses `NotionClient` and `SchemaManager`
- Minimal logic (delegates to core)

### `tools/pages.py`

**Purpose:** CRUD operations on pages

**Tools:**
- `notion_get_page` - Retrieve page
- `notion_get_data_source` - Get schema
- `notion_create_item` - Create page
- `notion_update_item` - Update page

**Notes:**
- Uses all core modules
- Includes validation (in progress)
- Handles Notion API format conversion

### `tools/content.py`

**Purpose:** Content/block operations

**Tools:**
- `notion_get_page_content` - Get content as markdown
- `notion_append_content` - Append blocks

**Notes:**
- Focuses on content, not properties
- Uses `BlockFormatter` extensively

### `server.py`

**Purpose:** FastMCP server initialization

**Responsibilities:**
- Create FastMCP instance
- Import tool modules (registers tools)
- Expose server for CLI

**Notes:**
- Very simple
- Just wires things together
- No business logic

## Data Flow

### Creating a Page

```
User (Claude)
    ↓ (MCP Protocol)
FastMCP
    ↓ (calls)
notion_create_item (tools/pages.py)
    ↓ (validates)
PropertyValidator (utils/validators.py)
    ↓ (fetches schema)
SchemaManager (core/schema.py)
    ↓ (HTTP request)
NotionClient (core/client.py)
    ↓ (API call)
Notion API
```

### Querying Pages

```
User (Claude)
    ↓
FastMCP
    ↓
notion_query (tools/query.py)
    ↓
SchemaManager (get data_source_id)
    ↓
NotionClient (POST query)
    ↓
Notion API
    ↓
Raw results
    ↓
PropertyFormatter (format for display)
    ↓
Formatted results → User
```

## Error Handling Strategy

### Layers

1. **NotionClient** - Converts HTTP errors to RuntimeError with helpful messages
2. **Tools** - Catch and re-raise with context
3. **FastMCP** - Surfaces errors to Claude

### Error Types

**Configuration Errors:**
- Missing token
- Missing database config
- Invalid YAML

**API Errors:**
- 401 Unauthorized (token/access)
- 404 Not Found (database/page)
- 400 Bad Request (validation)
- 429 Rate Limit

**Validation Errors:**
- Invalid property names
- Wrong property types
- Invalid select options
- Read-only properties

## Caching Strategy

### What Gets Cached

1. **Schemas** - `SchemaManager._schema_cache`
2. **Data Source IDs** - `SchemaManager._data_source_cache`

### Why Cache

- Reduces API calls
- Improves performance
- Notion schemas rarely change

### Cache Invalidation

```python
# Clear specific database
schema_manager.clear_cache("zettelkasten")

# Clear all
schema_manager.clear_cache()
```

## Testing Strategy

### Unit Tests (Core Modules)

```python
# Test formatters
formatter = PropertyFormatter()
title = formatter.extract_title(test_properties)
assert title == "Expected Title"

# Test validator
validator = PropertyValidator(test_schema)
is_valid, errors = validator.validate_properties(test_props)
assert is_valid == True
```

### Integration Tests (Tools)

```python
# Test with real Notion API
client = NotionClient()
result = await client.post("search", {"page_size": 1})
assert "results" in result
```

### End-to-End Tests

- Call MCP tools through FastMCP
- Verify actual Notion operations
- Test error handling

## Future Improvements

### Performance

- [ ] Batch operations
- [ ] Parallel requests
- [ ] Request pooling

### Features

- [ ] Advanced filtering DSL
- [ ] Webhook support
- [ ] Multi-workspace

### Code Quality

- [ ] Unit test coverage
- [ ] Integration test suite
- [ ] Type checking with mypy
- [ ] Linting with ruff

## Migration Notes

### From Old Architecture

**What Changed:**
1. Removed hardcoded database names
2. Removed config mutation
3. Split monolithic `notion_api.py` into modules
4. Added validation layer
5. Separated core from MCP concerns

**Breaking Changes:**
- None! Tools have same signatures
- Configuration moved to YAML

**Migration Steps:**
1. Create `databases.yaml` from old env vars
2. Update `.env` (same format)
3. Restart server
4. Everything works!

## Lessons Learned

### What Worked Well

✅ Separation of concerns made refactoring easy  
✅ No circular deps kept imports clean  
✅ Immutable config prevented bugs  
✅ Schema caching improved performance  

### What Was Challenging

⚠️ MCP boolean parameter handling  
⚠️ Notion API format complexity  
⚠️ FastMCP validation integration  

### Future Considerations

- Consider using Pydantic for validation
- Add OpenAPI/JSON Schema generation
- Implement retry logic for API calls
- Add telemetry/metrics

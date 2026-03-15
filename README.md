# Notion MCP Server

A production-grade Model Context Protocol (MCP) server for Notion, providing comprehensive database operations with schema validation and intelligent property handling.

## Features

- **🔧 Full CRUD Operations** - Create, read, update pages across Notion databases
- **🔍 Smart Search & Query** - Powerful filtering and search capabilities
- **📊 Schema Management** - Automatic schema fetching and validation
- **🎨 Content Formatting** - Markdown ↔ Notion blocks conversion
- **⚡ Async Architecture** - High-performance async operations
- **🛡️ Type Safety** - Comprehensive property validation
- **🔄 API 2025-09-03** - Uses latest Notion API with data sources

## Architecture

```
kas-fastmcp/
├── main.py                 # FastMCP server entry point
├── config.py              # Configuration management
├── notion_server/         # Core MCP server package
│   ├── core/             # Business logic (testable, reusable)
│   │   ├── client.py     # HTTP client wrapper
│   ├── formatters.py       # Property & block formatting
│   └── schema.py           # Schema fetching & caching
├── tools/                   # MCP tools (thin layer)
│   ├── query.py            # Search & discovery operations
│   ├── pages.py            # CRUD operations
│   └── content.py          # Content/blocks operations
├── utils/                   # Validators & helpers
│   └── validators.py       # Property validation
└── server.py               # FastMCP instance
```

### Design Principles

1. **Separation of Concerns** - Core logic separated from MCP layer
2. **No Circular Dependencies** - Clean, linear dependency flow
3. **Immutable Configuration** - Config is never mutated at runtime
4. **Schema-First** - Validate against actual Notion schemas
5. **Testable** - Each layer can be tested independently

## Installation

### Prerequisites

- Python 3.10+
- Notion Integration with API access
- Notion databases with integration added

### Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd kas-fastmcp
```

2. **Install dependencies**
```bash
uv sync
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your NOTION_TOKEN
```

4. **Configure databases**
```bash
cp databases.yaml.example databases.yaml
# Edit databases.yaml and add your database configurations
```

### Getting Your Notion Credentials

1. **Create Integration**
   - Go to https://www.notion.so/my-integrations
   - Click "New integration"
   - Give it a name and select your workspace
   - Copy the "Internal Integration Token"

2. **Get Data Source IDs**
   - Open your database in Notion
   - Click "..." menu → Settings
   - Manage data sources → Copy data source ID
   - Add to `databases.yaml`

3. **Add Integration to Databases**
   - Open each database in Notion
   - Click "..." menu → Connections
   - Add your integration

## Configuration

### `databases.yaml`

Define all your Notion databases:

```yaml
zettelkasten:
  data_source_id: "your-data-source-id-here"
  database_id: "your-database-id-here"
  title_property: "title"
  description: "Personal knowledge management"

habits:
  data_source_id: "your-data-source-id-here"
  database_id: "your-database-id-here"
  title_property: "title"
  description: "Habit tracking"
```

### `.env`

```bash
NOTION_TOKEN=ntn_your_token_here
NOTION_API_VERSION=2025-09-03
```

## Usage

### Running the Server

**Development:**
```bash
python main.py
```

**With FastMCP CLI:**
```bash
fastmcp run main.py
```

### Claude Desktop Integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "kas-notion": {
      "command": "python",
      "args": ["/path/to/kas-fastmcp/main.py"]
    }
  }
}
```

### Available Tools (14 total)

#### Query Tools (`query.py`)
- `notion_query` - Query pages from a database
- `notion_find_page_by_name` - Find page by exact title
- `notion_search` - Workspace-wide search
- `notion_list_data_sources` - List data sources for a database
- `notion_discover_databases` - Discover all accessible databases

#### Page Tools (`pages.py`)
- `notion_get_page` - Get page with properties (fully paginated when `include_content=True`)
- `notion_get_data_source` - Get database schema
- `notion_create_item` - Create new page
- `notion_update_item` - Update page properties

#### Content Tools (`content.py`)
- `notion_get_page_content` - Get page content as markdown
- `notion_append_content` - Append blocks to page

#### Schema Tools (`schema_sync.py`)
- `notion_sync_schemas` - Sync schemas from Notion and optionally update config
- `notion_validate_config` - Validate current database configuration

### Available Resources

- `notion://databases` - Lists all configured databases as JSON
- `notion://databases/{source_name}/schema` - Returns the cached schema for a specific database

## Testing

### Connection Testing

**Quick token verification:**
```bash
python connection_testing/token_verification.py
```

**Full connection test:**
```bash
python connection_testing/test_connection.py
```

This will:
- Validate your configuration
- Test API connectivity
- Check database access
- Fetch schemas

### Validation Testing

Test the property validator directly:
```bash
python test_validation.py
```

## Development

### Adding a New Database

1. Add to `databases.yaml`:
```yaml
my_database:
  data_source_id: "your-id"
  database_id: "your-id"
  title_property: "Name"
  description: "My new database"
```

2. No code changes needed! The server automatically loads all databases from the YAML file.

### Adding a New Tool

1. Choose the appropriate module (`query.py`, `pages.py`, or `content.py`)
2. Use the `@mcp.tool` decorator
3. Import and use core modules
4. Document with clear docstrings

Example:
```python
from notion_server.server import mcp
from notion_server.deps import _client  # shared singleton — do not instantiate a new one

@mcp.tool
async def my_new_tool(param: str) -> dict:
    """
    Tool description.

    Args:
        param: Parameter description

    Returns:
        Result description
    """
    result = await _client.get(f"endpoint/{param}")
    return result
```

### Project Structure Explained

**`core/`** - Pure business logic, no MCP dependencies
- Testable independently
- Reusable in other projects
- No side effects

**`tools/`** - MCP tool definitions
- Thin wrappers around core modules
- Handle MCP-specific concerns
- Minimal business logic

**`utils/`** - Shared utilities
- Validators
- Helpers
- Common functions

## Validation System

### How It Works

Properties are validated against Notion's schema before API calls:

```python
# Automatic validation
notion_create_item(
    source_name="zettelkasten",
    properties={
        "title": {"title": [{"text": {"content": "My Note"}, "type": "text"}]},
        "nonexistent": {"rich_text": [...]}  # ❌ Validation error!
    }
)
```

### What Gets Validated

✅ Property exists in schema  
✅ Property type matches  
✅ Select options are valid  
✅ Read-only properties rejected  
✅ Required properties present (strict mode)

### Direct Validation

Use the validator directly in your code:

```python
from notion_server.core import SchemaManager, NotionClient
from notion_server.utils import PropertyValidator

client = NotionClient()
schema_manager = SchemaManager(client)
schema = await schema_manager.get_schema("zettelkasten")

validator = PropertyValidator(schema)
is_valid, errors = validator.validate_properties(properties)
```

## Troubleshooting

### Common Issues

**"NOTION_TOKEN not found"**
- Create `.env` file from `.env.example`
- Add your token from https://www.notion.so/my-integrations

**"Database not found (404)"**
- Check database_id in `databases.yaml`
- Ensure integration is added to the database
- Verify integration has access

**"No databases configured"**
- Create `databases.yaml` from `databases.yaml.example`
- Add at least one database configuration

**"Property validation failed"**
- Check property names match your schema
- Ensure values are in correct Notion format
- Verify select options are valid

### Debug Mode

Enable detailed logging by checking server output:
```bash
python main.py 2>&1 | tee server.log
```

## API Reference

### NotionClient

```python
client = NotionClient(token=None, api_version=None)
await client.get(endpoint)
await client.post(endpoint, payload)
await client.patch(endpoint, payload)
```

### SchemaManager

```python
schema_manager = SchemaManager(client)
schema = await schema_manager.get_schema(source_name)
data_source_id = await schema_manager.get_data_source_id(source_name)
config = schema_manager.get_source_config(source_name)
```

### PropertyFormatter

```python
formatter = PropertyFormatter()
title = formatter.extract_title(properties)
formatted = formatter.format_for_display(properties)
```

### BlockFormatter

```python
formatter = BlockFormatter()
markdown = formatter.to_markdown(blocks)
blocks = formatter.from_markdown(markdown)
```

## Contributing

### Code Style

- Use type hints
- Write docstrings
- Keep functions focused
- Follow separation of concerns

### Testing

- Test core modules independently
- Test tools through MCP protocol
- Validate against real Notion databases

## License

MIT

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Uses Notion API 2025-09-03
- Developed for AI-powered productivity workflows

## Roadmap

- [x] Property validation on create and update
- [ ] Batch operations support
- [ ] Advanced filtering DSL
- [ ] Webhook support
- [ ] Multi-workspace support
- [ ] Enhanced markdown conversion (tables, callouts, etc.)

See [CHANGELOG.md](CHANGELOG.md) for a full history of changes.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Built with ❤️ for AI-powered productivity**

# Schema Synchronization

This directory includes powerful tools for keeping your local database configuration in sync with your Notion workspace. No more manual copying of property schemas or outdated configurations!

## Quick Start

### 🚀 One-Click Sync
```bash
python quick_sync.py sync
```
This will sync all your configured databases and update `databases.yaml` with the latest schemas.

### 🔍 Check Status  
```bash
python quick_sync.py status
```
Validates that all your configured databases are accessible and working.

### 🔍 Discover New Databases
```bash  
python quick_sync.py discover
```
Find databases in your Notion workspace that aren't configured yet.

## Advanced Usage

### Full CLI Tool
```bash
# Sync specific databases
python sync_schemas.py sync zettelkasten habits

# Sync all databases and update config
python sync_schemas.py sync --update-config

# Discover all available databases  
python sync_schemas.py discover

# Validate current configuration
python sync_schemas.py validate

# Silent mode for CI/CD
python sync_schemas.py sync --quiet --update-config
```

### Using the Bash Wrapper
```bash
# The sync-schemas script automatically handles virtual environments
./sync-schemas sync --update-config
./sync-schemas discover
./sync-schemas validate
```

## MCP Tools

If you're using the MCP server, you also have access to these tools:

### `notion_sync_schemas`
Sync database schemas from within the MCP environment:
```python
# Sync all databases
await notion_sync_schemas()

# Sync specific databases and update config
await notion_sync_schemas(
    source_names=["zettelkasten", "habits"],
    update_config=True
)
```

### `notion_discover_databases`
Find databases you haven't configured yet:
```python
result = await notion_discover_databases()
print(f"Found {result['total_found']} databases")
print(f"Unconfigured: {len(result['unconfigured'])}")
```

### `notion_validate_config`
Check if your configuration is working:
```python
result = await notion_validate_config()
if result["overall_status"] == "healthy":
    print("✅ All good!")
```

## What Gets Synced

When you sync schemas, the tool fetches:

- **Property definitions** - Names, types, and constraints
- **Select/multi-select options** - All available choices
- **Status options** - Available status values  
- **Title property** - Which property serves as the title
- **Database metadata** - Title, description, URLs

## Configuration Updates

When you use `--update-config`, the tool:

1. **Fetches fresh schemas** from Notion API
2. **Updates databases.yaml** with current schema information
3. **Creates a timestamped backup** of your old config
4. **Adds missing data_source_ids** if they weren't configured
5. **Adds last_sync timestamps** for tracking

### Example Updated Config
```yaml
zettelkasten:
  data_source_id: "1d58645d-6355-8021-8111-000b41f7d430"
  database_id: "1d58645d635580cc903acb164bb969b3"
  title_property: "title"
  description: "Personal knowledge management system"
  last_sync: "2026-01-22T22:30:15.123456"
  schema:
    title:
      type: "title"
      id: "title"
    tags:
      type: "multi_select" 
      id: "abc123"
      options: ["research", "personal", "work"]
    status:
      type: "status"
      id: "def456"  
      options: ["Not started", "In progress", "Complete"]
```

## Error Handling

The sync tools are designed to be robust:

- **Invalid databases** - Skipped with clear error messages
- **Network issues** - Retryable with proper error reporting  
- **Configuration problems** - Detected and reported with fixes
- **Backup protection** - Your original config is always backed up

## Integration Tips

### Daily Workflow
Add this to your daily routine:
```bash
# Quick status check
python quick_sync.py status

# If schemas are stale, sync them
python quick_sync.py sync
```

### CI/CD Pipeline
```bash
# Validate configuration in CI
python sync_schemas.py validate --quiet

# Auto-sync in deployment pipeline  
python sync_schemas.py sync --quiet --update-config
```

### IDE Integration
You can run the quick sync tool directly from your editor:
- **VS Code**: Add as a task in `.vscode/tasks.json`
- **PyCharm**: Add as an external tool
- **Terminal**: Alias `notion-sync` to `python quick_sync.py`

## Troubleshooting

### "Database not found" errors
Run discovery to see available databases:
```bash
python sync_schemas.py discover
```

### "Permission denied" errors  
Check your Notion token has access to the databases:
```bash
python sync_schemas.py validate
```

### "Schema validation failed" errors
Your local schema is outdated. Sync to refresh:
```bash
python sync_schemas.py sync --update-config
```

### Missing data_source_id
The sync tool will automatically add missing data_source_ids:
```bash
python sync_schemas.py sync --update-config
```

## Benefits

✅ **Always current schemas** - No more outdated property definitions  
✅ **Catch breaking changes** - Know when Notion properties change  
✅ **Faster development** - No manual config management  
✅ **Better validation** - Accurate property validation  
✅ **CI/CD friendly** - Automate schema updates in pipelines  
✅ **Discovery mode** - Find databases you haven't configured  

This makes your FastMCP server much more maintainable and keeps it in perfect sync with your evolving Notion workspace!

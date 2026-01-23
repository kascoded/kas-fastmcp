"""
Schema Synchronization Tools
Tools for syncing database schemas and configurations between Notion and local config.
"""

from typing import Dict, Any, List, Optional
from notion_server.server import mcp
from notion_server.core import NotionClient, SchemaManager
from config import NotionConfig
import yaml
from pathlib import Path
import datetime


# Initialize core modules
_client = NotionClient()
_schema_manager = SchemaManager(_client)


@mcp.tool
async def notion_sync_schemas(
    source_names: Optional[List[str]] = None,
    update_config: bool = False
) -> Dict[str, Any]:
    """
    Sync schemas from Notion for one or more databases.
    Fetches current schema information and optionally updates local config.
    
    Args:
        source_names: List of database names to sync, or None for all configured databases
        update_config: Whether to update databases.yaml with fetched schemas
    
    Returns:
        Sync results with schema information and any config updates
    """
    if source_names is None:
        source_names = list(NotionConfig.DATABASES.keys())
    
    results = {}
    updated_configs = {}
    errors = []
    
    for source_name in source_names:
        try:
            # Clear cache to force fresh fetch
            _schema_manager.clear_cache(source_name)
            
            # Fetch fresh schema
            schema = await _schema_manager.get_schema(source_name)
            data_source_id = await _schema_manager.get_data_source_id(source_name)
            
            # Get additional metadata
            ds_result = await _client.get(f"data_sources/{data_source_id}")
            title_array = ds_result.get("title", [])
            title = title_array[0].get("plain_text", "Untitled") if title_array else "Untitled"
            
            results[source_name] = {
                "status": "success",
                "data_source_id": data_source_id,
                "title": title,
                "properties": schema,
                "property_count": len(schema),
                "url": ds_result.get("url")
            }
            
            if update_config:
                # Prepare config update
                current_config = NotionConfig.get_database_config(source_name)
                updated_config = current_config.copy()
                updated_config["schema"] = schema
                updated_config["last_sync"] = datetime.datetime.utcnow().isoformat()
                
                # Ensure we have data_source_id in config
                if not updated_config.get("data_source_id"):
                    updated_config["data_source_id"] = data_source_id
                
                updated_configs[source_name] = updated_config
                
        except Exception as e:
            errors.append(f"{source_name}: {str(e)}")
            results[source_name] = {
                "status": "error",
                "error": str(e)
            }
    
    # Update config file if requested and we have updates
    config_updated = False
    if update_config and updated_configs:
        try:
            config_updated = _update_databases_yaml(updated_configs)
        except Exception as e:
            errors.append(f"Config update failed: {str(e)}")
    
    return {
        "synced_databases": len([r for r in results.values() if r.get("status") == "success"]),
        "total_requested": len(source_names),
        "results": results,
        "errors": errors,
        "config_updated": config_updated,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }


@mcp.tool
async def notion_discover_databases() -> Dict[str, Any]:
    """
    Discover all available databases in the Notion workspace.
    Useful for finding new databases to add to configuration.
    
    Returns:
        List of discovered databases with their IDs and basic information
    """
    # First get all data sources
    payload = {
        "filter": {"property": "object", "value": "data_source"},
        "page_size": 100
    }
    result = await _client.post("search", payload)
    
    discovered = []
    configured_ids = set()
    
    # Get currently configured database and data source IDs
    for db_config in NotionConfig.DATABASES.values():
        if db_config.get("database_id"):
            configured_ids.add(db_config["database_id"])
        if db_config.get("data_source_id"):
            configured_ids.add(db_config["data_source_id"])
    
    for ds in result.get("results", []):
        title_array = ds.get("title", [])
        title = title_array[0].get("plain_text", "Untitled") if title_array else "Untitled"
        
        ds_id = ds.get("id")
        parent = ds.get("parent", {})
        db_id = parent.get("database_id") if parent.get("type") == "database" else None
        
        is_configured = ds_id in configured_ids or (db_id and db_id in configured_ids)
        
        discovered.append({
            "data_source_id": ds_id,
            "database_id": db_id,
            "title": title,
            "url": ds.get("url"),
            "is_configured": is_configured,
            "suggested_name": _suggest_config_name(title)
        })
    
    return {
        "discovered_databases": discovered,
        "total_found": len(discovered),
        "unconfigured": [db for db in discovered if not db["is_configured"]],
        "configured": [db for db in discovered if db["is_configured"]]
    }


@mcp.tool
async def notion_validate_config() -> Dict[str, Any]:
    """
    Validate current database configuration against Notion workspace.
    Checks if all configured databases are accessible and IDs are valid.
    
    Returns:
        Validation results for each configured database
    """
    results = {}
    errors = []
    
    for source_name in NotionConfig.list_databases():
        try:
            config = NotionConfig.get_database_config(source_name)
            
            # Test data source ID resolution
            try:
                data_source_id = await _schema_manager.get_data_source_id(source_name)
                
                # Test actual API access
                ds_result = await _client.get(f"data_sources/{data_source_id}")
                
                title_array = ds_result.get("title", [])
                title = title_array[0].get("plain_text", "Untitled") if title_array else "Untitled"
                
                results[source_name] = {
                    "status": "valid",
                    "data_source_id": data_source_id,
                    "database_id": config.get("database_id"),
                    "title": title,
                    "url": ds_result.get("url"),
                    "has_schema_in_config": NotionConfig.has_schema(source_name)
                }
                
            except Exception as api_error:
                results[source_name] = {
                    "status": "invalid",
                    "error": str(api_error),
                    "config": config
                }
                errors.append(f"{source_name}: {str(api_error)}")
                
        except Exception as config_error:
            results[source_name] = {
                "status": "config_error", 
                "error": str(config_error)
            }
            errors.append(f"{source_name}: Config error - {str(config_error)}")
    
    valid_count = len([r for r in results.values() if r.get("status") == "valid"])
    
    return {
        "valid_databases": valid_count,
        "total_configured": len(results),
        "results": results,
        "errors": errors,
        "overall_status": "healthy" if len(errors) == 0 else "issues_found"
    }


def _update_databases_yaml(updated_configs: Dict[str, Dict[str, Any]]) -> bool:
    """
    Update the databases.yaml file with new configurations.
    
    Args:
        updated_configs: Dictionary of source_name -> updated config
        
    Returns:
        True if file was updated successfully
    """
    yaml_path = Path(__file__).parent.parent.parent / "databases.yaml"
    
    if not yaml_path.exists():
        raise FileNotFoundError("databases.yaml not found - cannot update config")
    
    # Load current YAML
    with open(yaml_path, "r") as f:
        content = f.read()
    
    # Parse as YAML to maintain structure
    current_data = yaml.safe_load(content) or {}
    
    # Update with new configs
    for source_name, config in updated_configs.items():
        current_data[source_name] = config
    
    # Create backup
    backup_path = yaml_path.with_suffix(f".yaml.backup.{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
    yaml_path.rename(backup_path)
    
    # Write updated YAML
    with open(yaml_path, "w") as f:
        f.write("# Notion Databases Configuration\n")
        f.write("# Last updated: " + datetime.datetime.utcnow().isoformat() + "\n")
        f.write("# \n")
        f.write("# Each database entry requires either:\n")
        f.write("#   - data_source_id (preferred for API 2025-09-03)\n")
        f.write("#   - database_id (will auto-resolve data_source_id)\n")
        f.write("#\n")
        f.write("# Optional fields:\n")
        f.write("#   - title_property: Name of the title property (default: \"title\")\n")
        f.write("#   - description: Human-readable description\n")
        f.write("#   - schema: Property definitions (synced from Notion API)\n")
        f.write("#   - last_sync: Last schema sync timestamp\n\n")
        
        yaml.dump(current_data, f, default_flow_style=False, indent=2, sort_keys=False)
    
    print(f"Updated databases.yaml (backup saved to {backup_path.name})")
    return True


def _suggest_config_name(title: str) -> str:
    """
    Suggest a configuration name based on database title.
    
    Args:
        title: Database title from Notion
        
    Returns:
        Suggested config name (lowercase, underscores)
    """
    import re
    # Convert to lowercase and replace spaces/special chars with underscores
    name = re.sub(r'[^a-zA-Z0-9_]', '_', title.lower())
    # Remove multiple consecutive underscores
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    return name or "untitled_database"

#!/usr/bin/env python3
"""
Schema Sync Utility
Standalone script to sync database schemas from Notion to local configuration.
Can be run manually or as part of CI/CD pipelines.
"""

import asyncio
import argparse
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import NotionConfig
from notion_server.core import NotionClient, SchemaManager
import datetime


class SchemaSyncer:
    """Handles schema synchronization operations."""
    
    def __init__(self):
        """Initialize the syncer with Notion client."""
        try:
            NotionConfig.validate()
            self.client = NotionClient()
            self.schema_manager = SchemaManager(self.client)
        except ValueError as e:
            print(f"❌ Configuration Error:\n{e}")
            sys.exit(1)
    
    async def sync_schemas(
        self, 
        source_names: Optional[List[str]] = None,
        update_config: bool = False,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Sync schemas from Notion for specified databases.
        
        Args:
            source_names: List of database names to sync, or None for all
            update_config: Whether to update databases.yaml
            verbose: Whether to print progress information
            
        Returns:
            Dictionary with sync results
        """
        if source_names is None:
            source_names = list(NotionConfig.DATABASES.keys())
        
        if verbose:
            print(f"📡 Syncing {len(source_names)} database schemas from Notion...")
        
        results = {}
        updated_configs = {}
        errors = []
        
        for i, source_name in enumerate(source_names, 1):
            if verbose:
                print(f"  [{i}/{len(source_names)}] {source_name}...", end=" ")
            
            try:
                # Clear cache to force fresh fetch
                self.schema_manager.clear_cache(source_name)
                
                # Fetch fresh schema and metadata
                schema = await self.schema_manager.get_schema(source_name)
                data_source_id = await self.schema_manager.get_data_source_id(source_name)
                
                ds_result = await self.client.get(f"data_sources/{data_source_id}")
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
                
                if verbose:
                    print(f"✅ {len(schema)} properties")
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
                error_msg = f"{source_name}: {str(e)}"
                errors.append(error_msg)
                results[source_name] = {
                    "status": "error",
                    "error": str(e)
                }
                
                if verbose:
                    print(f"❌ Error: {str(e)}")
        
        # Update config file if requested and we have updates
        config_updated = False
        if update_config and updated_configs:
            if verbose:
                print(f"📝 Updating databases.yaml with {len(updated_configs)} schemas...")
            
            try:
                config_updated = self._update_databases_yaml(updated_configs)
                if verbose and config_updated:
                    print("✅ Configuration file updated successfully")
            except Exception as e:
                error_msg = f"Config update failed: {str(e)}"
                errors.append(error_msg)
                if verbose:
                    print(f"❌ {error_msg}")
        
        return {
            "synced_databases": len([r for r in results.values() if r.get("status") == "success"]),
            "total_requested": len(source_names),
            "results": results,
            "errors": errors,
            "config_updated": config_updated,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
    
    async def discover_databases(self, verbose: bool = True) -> Dict[str, Any]:
        """
        Discover all available databases in the Notion workspace.
        
        Args:
            verbose: Whether to print discovery information
            
        Returns:
            Dictionary with discovered databases
        """
        if verbose:
            print("🔍 Discovering databases in Notion workspace...")
        
        # Get all data sources
        payload = {
            "filter": {"property": "object", "value": "data_source"},
            "page_size": 100
        }
        result = await self.client.post("search", payload)
        
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
                "suggested_name": self._suggest_config_name(title)
            })
        
        if verbose:
            unconfigured = [db for db in discovered if not db["is_configured"]]
            configured = [db for db in discovered if db["is_configured"]]
            
            print(f"📊 Found {len(discovered)} total databases")
            print(f"   ✅ {len(configured)} already configured")
            print(f"   ⚠️  {len(unconfigured)} not configured")
            
            if unconfigured:
                print("\n🆕 Unconfigured databases:")
                for db in unconfigured:
                    print(f"   • {db['title']} (suggested name: {db['suggested_name']})")
                    print(f"     data_source_id: {db['data_source_id']}")
                    if db['database_id']:
                        print(f"     database_id: {db['database_id']}")
                    print()
        
        return {
            "discovered_databases": discovered,
            "total_found": len(discovered),
            "unconfigured": [db for db in discovered if not db["is_configured"]],
            "configured": [db for db in discovered if db["is_configured"]]
        }
    
    async def validate_config(self, verbose: bool = True) -> Dict[str, Any]:
        """
        Validate current database configuration against Notion workspace.
        
        Args:
            verbose: Whether to print validation information
            
        Returns:
            Dictionary with validation results
        """
        if verbose:
            print("🔍 Validating database configuration...")
        
        results = {}
        errors = []
        
        for source_name in NotionConfig.list_databases():
            if verbose:
                print(f"  • {source_name}...", end=" ")
            
            try:
                config = NotionConfig.get_database_config(source_name)
                
                # Test data source ID resolution and API access
                data_source_id = await self.schema_manager.get_data_source_id(source_name)
                ds_result = await self.client.get(f"data_sources/{data_source_id}")
                
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
                
                if verbose:
                    schema_status = "with schema" if results[source_name]["has_schema_in_config"] else "no schema"
                    print(f"✅ Valid ({schema_status})")
                    
            except Exception as e:
                error_msg = str(e)
                results[source_name] = {
                    "status": "invalid",
                    "error": error_msg,
                }
                errors.append(f"{source_name}: {error_msg}")
                
                if verbose:
                    print(f"❌ {error_msg}")
        
        valid_count = len([r for r in results.values() if r.get("status") == "valid"])
        
        if verbose:
            if errors:
                print(f"\n⚠️  Issues found:")
                for error in errors:
                    print(f"   • {error}")
            else:
                print(f"\n✅ All {valid_count} configured databases are valid")
        
        return {
            "valid_databases": valid_count,
            "total_configured": len(results),
            "results": results,
            "errors": errors,
            "overall_status": "healthy" if len(errors) == 0 else "issues_found"
        }
    
    def _update_databases_yaml(self, updated_configs: Dict[str, Dict[str, Any]]) -> bool:
        """Update the databases.yaml file with new configurations."""
        yaml_path = Path(__file__).parent.parent / "databases.yaml"
        
        if not yaml_path.exists():
            raise FileNotFoundError("databases.yaml not found - cannot update config")
        
        # Load current YAML content
        with open(yaml_path, "r") as f:
            content = f.read()
        
        # Parse as YAML to maintain structure
        current_data = yaml.safe_load(content) or {}
        
        # Update with new configs
        for source_name, config in updated_configs.items():
            current_data[source_name] = config
        
        # Create backup
        backup_path = yaml_path.with_suffix(f".yaml.backup.{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
        with open(yaml_path, "r") as src, open(backup_path, "w") as dst:
            dst.write(src.read())
        
        # Write updated YAML with proper header
        with open(yaml_path, "w") as f:
            f.write("# Notion Databases Configuration\n")
            f.write(f"# Last updated: {datetime.datetime.utcnow().isoformat()}\n")
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
        
        return True
    
    @staticmethod
    def _suggest_config_name(title: str) -> str:
        """Suggest a configuration name based on database title."""
        import re
        # Convert to lowercase and replace spaces/special chars with underscores
        name = re.sub(r'[^a-zA-Z0-9_]', '_', title.lower())
        # Remove multiple consecutive underscores
        name = re.sub(r'_+', '_', name)
        # Remove leading/trailing underscores
        name = name.strip('_')
        return name or "untitled_database"


async def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(
        description="Sync database schemas between Notion and local configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s sync --update-config          # Sync all databases and update config
  %(prog)s sync zettelkasten habits      # Sync specific databases
  %(prog)s discover                      # Find all available databases
  %(prog)s validate                      # Validate current configuration
  %(prog)s sync --quiet --update-config  # Silent sync for CI/CD
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync database schemas from Notion')
    sync_parser.add_argument(
        'databases', 
        nargs='*', 
        help='Database names to sync (default: all configured)'
    )
    sync_parser.add_argument(
        '--update-config', 
        action='store_true',
        help='Update databases.yaml with synced schemas'
    )
    sync_parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress output'
    )
    
    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover all available databases')
    discover_parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress output'
    )
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate current configuration')
    validate_parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress output'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    syncer = SchemaSyncer()
    
    try:
        if args.command == 'sync':
            result = await syncer.sync_schemas(
                source_names=args.databases or None,
                update_config=args.update_config,
                verbose=not args.quiet
            )
            
            if not args.quiet:
                success_count = result["synced_databases"]
                total_count = result["total_requested"]
                
                if result["errors"]:
                    print(f"\n❌ Completed with errors: {success_count}/{total_count} successful")
                    sys.exit(1)
                else:
                    print(f"\n✅ Successfully synced {success_count}/{total_count} databases")
                    
        elif args.command == 'discover':
            await syncer.discover_databases(verbose=not args.quiet)
            
        elif args.command == 'validate':
            result = await syncer.validate_config(verbose=not args.quiet)
            
            if result["errors"]:
                if not args.quiet:
                    print(f"\n❌ Validation failed: {len(result['errors'])} issues found")
                sys.exit(1)
            else:
                if not args.quiet:
                    print(f"\n✅ All {result['valid_databases']} databases validated successfully")
                    
    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

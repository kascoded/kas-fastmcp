#!/usr/bin/env python3
"""
Quick Schema Operations
Simple CLI for common schema sync tasks.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sync_schemas import SchemaSyncer


async def quick_sync():
    """Quick sync of all databases with config update."""
    print("🚀 Quick Sync: Updating all database schemas...")
    syncer = SchemaSyncer()
    
    result = await syncer.sync_schemas(
        source_names=None,
        update_config=True,
        verbose=True
    )
    
    if result["errors"]:
        print(f"\n❌ Sync completed with {len(result['errors'])} errors")
        for error in result["errors"]:
            print(f"   • {error}")
        return False
    else:
        print(f"\n✅ Successfully synced {result['synced_databases']} databases")
        print("📝 Configuration updated!")
        return True


async def quick_status():
    """Quick validation of current configuration."""
    print("🔍 Quick Status: Validating configuration...")
    syncer = SchemaSyncer()
    
    result = await syncer.validate_config(verbose=True)
    
    if result["errors"]:
        print(f"\n❌ Found {len(result['errors'])} configuration issues")
        return False
    else:
        print(f"\n✅ All {result['valid_databases']} databases are healthy")
        return True


async def quick_discover():
    """Quick discovery of available databases."""
    print("🔍 Quick Discovery: Finding available databases...")
    syncer = SchemaSyncer()
    
    result = await syncer.discover_databases(verbose=True)
    
    unconfigured = result["unconfigured"]
    if unconfigured:
        print(f"\n💡 Found {len(unconfigured)} databases that could be added to your configuration:")
        for db in unconfigured[:5]:  # Show first 5
            print(f"   Add to databases.yaml:")
            print(f"   {db['suggested_name']}:")
            print(f"     data_source_id: \"{db['data_source_id']}\"")
            if db['database_id']:
                print(f"     database_id: \"{db['database_id']}\"")
            print(f"     description: \"{db['title']}\"")
            print()
        
        if len(unconfigured) > 5:
            print(f"   ... and {len(unconfigured) - 5} more")
    
    return True


async def main():
    """Main CLI interface."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
    else:
        # Interactive mode
        print("Schema Sync Quick Actions")
        print("=======================")
        print("1. Sync all schemas (update config)")
        print("2. Check status (validate config)")  
        print("3. Discover databases")
        print("4. Exit")
        
        try:
            choice = input("\nSelect an option (1-4): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Goodbye!")
            return
        
        command = {
            '1': 'sync',
            '2': 'status', 
            '3': 'discover',
            '4': 'exit'
        }.get(choice, 'help')
    
    try:
        if command in ['sync', 's']:
            success = await quick_sync()
            sys.exit(0 if success else 1)
            
        elif command in ['status', 'validate', 'v']:
            success = await quick_status()
            sys.exit(0 if success else 1)
            
        elif command in ['discover', 'd']:
            success = await quick_discover()
            sys.exit(0 if success else 1)
            
        elif command in ['exit', 'quit', 'q']:
            print("👋 Goodbye!")
            
        else:
            print("Usage: python quick_sync.py [sync|status|discover]")
            print()
            print("Commands:")
            print("  sync     - Sync all schemas and update config")
            print("  status   - Validate current configuration") 
            print("  discover - Find available databases")
            print()
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

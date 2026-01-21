#!/usr/bin/env python3
"""
Test Notion API connection and configuration.
Dynamically tests all databases configured in databases.yaml.
"""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import NotionConfig
from notion_server.core import NotionClient, SchemaManager


async def test_notion_connection():
    """Test Notion API connection step by step."""
    
    print("=" * 70)
    print("NOTION CONNECTION TESTER")
    print("=" * 70)
    
    # Step 1: Validate configuration
    print("\n1. Validating configuration...")
    try:
        NotionConfig.validate()
        print("   ✓ Configuration valid")
        print(f"   ✓ API Version: {NotionConfig.API_VERSION}")
        print(f"   ✓ Token format: {NotionConfig.TOKEN[:10]}...")
    except ValueError as e:
        print(f"   ❌ Configuration error:\n{e}")
        return False
    
    # Step 2: List configured databases
    print("\n2. Configured databases:")
    databases = NotionConfig.list_databases()
    for db_name in databases:
        config = NotionConfig.get_database_config(db_name)
        print(f"   • {db_name}")
        if config.get("description"):
            print(f"     Description: {config['description']}")
        if config.get("database_id"):
            print(f"     Database ID: {config['database_id'][:20]}...")
        if config.get("data_source_id"):
            print(f"     Data Source ID: {config['data_source_id'][:20]}...")
        print(f"     Title Property: {config.get('title_property', 'title')}")
    
    # Step 3: Test API connection
    print("\n3. Testing API connection...")
    client = NotionClient()
    schema_manager = SchemaManager(client)
    
    try:
        # Test basic connectivity with search
        print("   Testing /v1/search endpoint...")
        search_result = await client.post("search", {"page_size": 1})
        print(f"   ✓ Search successful")
        
        # Test each configured database
        print("\n4. Testing database access...")
        for db_name in databases:
            print(f"\n   Testing '{db_name}':")
            
            try:
                # Get data source ID (may fetch from API)
                data_source_id = await schema_manager.get_data_source_id(db_name)
                print(f"     ✓ Data source resolved: {data_source_id[:20]}...")
                
                # Try to query the database
                query_result = await client.post(
                    f"data_sources/{data_source_id}/query",
                    {"page_size": 1}
                )
                
                results = query_result.get("results", [])
                print(f"     ✓ Query successful ({len(results)} page(s) found)")
                
                # Try to fetch schema
                schema = await schema_manager.get_schema(db_name)
                prop_count = len(schema)
                print(f"     ✓ Schema fetched ({prop_count} properties)")
                
                # Show a few properties
                if prop_count > 0:
                    sample_props = list(schema.keys())[:3]
                    print(f"     Sample properties: {', '.join(sample_props)}")
                
            except Exception as e:
                print(f"     ❌ Failed: {str(e)}")
                if "401" in str(e):
                    print(f"     → Integration not added to this database")
                    print(f"     → Go to database settings and add your integration")
                elif "404" in str(e):
                    print(f"     → Database or data source not found")
                    print(f"     → Check IDs in databases.yaml")
        
        print("\n" + "=" * 70)
        print("✓ CONNECTION TEST COMPLETE")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Fix any failed database connections above")
        print("  2. Run your MCP server: bash run_mcp.sh")
        print("  3. Test tools in Claude Desktop")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Connection test failed: {str(e)}")
        await diagnose_error(str(e))
        return False


async def diagnose_error(error_message: str):
    """Provide specific guidance based on error message."""
    print("\n🔍 Error Diagnosis:")
    
    if "401" in error_message or "unauthorized" in error_message.lower():
        print("""
Common causes of 401 errors:
  1. Invalid token - Check NOTION_TOKEN in .env
  2. Integration not added to database
     → Open database in Notion
     → Click "..." menu → Connections
     → Add your integration
  3. Token expired - Generate new token at notion.so/my-integrations
        """)
    elif "404" in error_message:
        print("""
Common causes of 404 errors:
  1. Incorrect database_id or data_source_id in databases.yaml
  2. Database deleted or moved
  3. Integration doesn't have access
        """)
    elif "timeout" in error_message.lower():
        print("""
Connection timeout:
  1. Check your internet connection
  2. Try again - might be temporary Notion API issue
        """)
    else:
        print(f"""
Unexpected error. Check:
  1. Your .env file has valid NOTION_TOKEN
  2. Your databases.yaml has correct IDs
  3. Your integration has proper permissions
        """)


if __name__ == "__main__":
    try:
        success = asyncio.run(test_notion_connection())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python3
"""
Notion Assistant MCP Server
Entry point for the FastMCP-based Notion integration.
"""
import sys
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Import configuration and validate
from config import NotionConfig

# Validate configuration before starting server
try:
    NotionConfig.validate()
    print("✓ Configuration validated successfully", file=sys.stderr)
    print(f"✓ Using Notion API version: {NotionConfig.API_VERSION}", file=sys.stderr)
    print(f"✓ Configured databases: {list(NotionConfig.DATABASES.keys())}", file=sys.stderr)
except ValueError as e:
    print(f"❌ Configuration Error:\n{e}", file=sys.stderr)
    print("\nPlease check your .env file and ensure all required variables are set.", file=sys.stderr)
    sys.exit(1)

# Import and expose the server for FastMCP
# FastMCP's CLI looks for 'mcp', 'server', or 'app' in the module
from notion_server.server import mcp

if __name__ == "__main__":
    print("Starting Notion Assistant MCP Server...", file=sys.stderr)
    try:
        # Run the FastMCP server
        mcp.run()
    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"❌ Server error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
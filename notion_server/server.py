# notion_server/server.py
from config import NotionConfig
from fastmcp import FastMCP

# Create the MCP instance
mcp = FastMCP("KasNotionMCP")

# Import tools AFTER defining mcp to avoid circular import
from notion_server.tools import notion_api

# Optional: run server
if __name__ == "__main__":
    mcp.run()

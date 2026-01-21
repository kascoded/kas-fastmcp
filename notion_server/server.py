"""
FastMCP Server Instance
This module creates the FastMCP server instance that will be used by the tools.
"""
from config import NotionConfig
from fastmcp import FastMCP

# Create the MCP server instance with a standard name
# FastMCP looks for variables named: mcp, server, or app
server = FastMCP("KasNotionMCP")

# For compatibility, also expose as 'mcp'
mcp = server

# Import tools AFTER defining mcp to avoid circular import
# The @mcp.tool decorators will register when this module is imported
from notion_server import tools

# Optional: run server directly from this file
if __name__ == "__main__":
    server.run()
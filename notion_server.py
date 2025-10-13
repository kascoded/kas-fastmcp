from fastmcp import FastMCP
from tools import notion_api  # automatically loads the decorated tools

mcp = FastMCP("KasNotionMCP")

# Register tools from notion_api
mcp.import_module(notion_api)

# Optional: start MCP locally
if __name__ == "__main__":
    mcp.run()

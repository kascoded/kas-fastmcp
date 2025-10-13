from fastmcp import FastMCP

# Initialize your FastMCP app
mcp = FastMCP("KasNotionMCP")

# Import the Notion tools so that @mcp.tool decorators register automatically
import tools.notion_api  # ensure __init__.py exists in 'tools' folder

app = mcp  # exported for main.py

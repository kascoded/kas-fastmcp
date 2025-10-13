import os
from fastmcp import FastMCP
from tools import notion_api  # automatically registers tools

mcp = FastMCP("KasNotionMCP")

if __name__ == "__main__":
    mcp.run()

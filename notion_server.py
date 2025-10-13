from fastmcp import FastMCP
from tools import notion_api  # this import triggers tool registration

mcp = FastMCP("KasNotionMCP")

if __name__ == "__main__":
    mcp.run()

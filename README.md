# 🧠 Kas Notion MCP

A modular **FastMCP 2.0 server** that provides tools for querying and retrieving data from Notion databases and data sources.  
Built for integration with **OpenAI AgentKit** and **FastMCP Cloud**, this server forms the foundation of Kas’s Notion-aware automation layer.

---

## 📁 Project Structure

kas-fastmcp/
├── notion_server/
│ ├── init.py
│ └── server.py # Defines the FastMCP server (KasNotionMCP)
├── tools/
│ ├── init.py
│ └── notion_api.py # Contains Notion API tools
├── main.py # Entrypoint to run the server
├── requirements.txt
├── pyproject.toml
└── README.md

---

## ⚙️ Environment Variables

Create a `.env` file or configure these in **FastMCP Cloud**:

| Variable | Description | Required |
|-----------|--------------|-----------|
| `NOTION_TOKEN` | Your Notion internal integration token | ✅ |
| `NOTION_DATABASE_ID` | Default database ID for quick queries | optional |
| `NOTION_DATA_SOURCE_ID` | Default data source ID (for 2025-09-03 API) | optional |
| `NOTION_API_VERSION` | Notion API version (default `2022-06-28`) | optional |

---

## 🚀 Local Setup

### 1. Clone & create virtual environment
```bash
git clone https://github.com/<your-username>/kas-fastmcp.git
cd kas-fastmcp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
2. Run the server
python main.py
Expected output:
FastMCP 2.0
Server name: KasNotionMCP
Transport: STDIO
The MCP will now listen for incoming requests (e.g. from AgentKit or another client).
🧰 Available Tools
Tool	Description
notion_query_database	Query a Notion database via /v1/databases/{id}/query
notion_query_data_source	Query a Notion data source via /v1/data_sources/{id}/query
notion_get_page	Retrieve a Notion page by ID
Each tool returns the raw JSON response from the Notion API.
☁️ Deploying to FastMCP Cloud
Push this repo to GitHub
Go to https://fastmcp.cloud
Import your repository
Add your environment variables
Deploy 🚀
Cloud will auto-detect:
FastMCP entrypoint in main.py
Dependencies from requirements.txt
After deployment, you’ll get a URL like:
https://fastmcp.cloud/<your-username>/kas-notion-mcp
🤖 Connecting to OpenAI AgentKit
In OpenAI Agent Builder → Tools → Add MCP Tool:
Paste your FastMCP Cloud URL
AgentKit will automatically discover the available tools:
notion_query_database
notion_query_data_source
notion_get_page
You can now issue natural-language commands such as:
“Query my Notion database for pages tagged Zettelkasten sorted by last edited.”
🧱 Extending
Add new tools in tools/notion_api.py, for example:
@mcp.tool(description="Create a new page in Notion")
def notion_create_page(title: str, parent_database_id: Optional[str] = None) -> Dict[str, Any]:
    ...
FastMCP automatically registers new tools when the file is imported.
💡 Developer Notes
Why separate main.py and server.py?
server.py defines what the MCP is (its tools and logic).
main.py defines how to start it.
This separation makes deployment cleaner, avoids circular imports, and prepares the project for multi-server setups (e.g., adding habit_server.py, zettel_server.py, etc.).
Future Expansion
You can scale this structure into a multi-tool MCP suite:
kas-fastmcp/
├── notion_server/
├── habit_server/
├── zettel_server/
└── main.py
Each module would define its own FastMCP tools and be deployable independently or merged into one super-server.
📄 License
MIT © 2025 Miras Kasymkhan

---

Would you like me to include badges (like Python version, FastMCP Cloud deploy status,
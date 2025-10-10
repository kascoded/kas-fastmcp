# Kas Notion MCP Server

This repository contains a lightweight **FastMCP** server that connects to **Notion** for intelligent note-taking, logging, and querying.  
It’s designed to work with **FastMCP Cloud** and the **OpenAI Agent Builder** to automate Zettelkasten entries, daily notes, and habit tracking.

---

## Getting Started

This repository includes a ready-to-deploy MCP server that integrates with Notion and exposes a set of tools for structured data logging.

### Files

- `notion_server.py` – Main MCP server exposing Notion tools  
- `test_client.py` – Example script for local testing  
- `requirements.txt` – Project dependencies  

---

## Deployment

This repository is ready to be deployed to **FastMCP Cloud**.

1. Create a new [FastMCP Cloud account](https://fastmcp.cloud/signup)  
2. Connect your GitHub repository  
3. Set the **Entrypoint** to `notion_server.py:mcp`  
4. Add your Notion environment variables in the project settings  
5. Deploy — a public endpoint will be generated automatically  

---

## Environment Variables

Set the following environment variables in **FastMCP Cloud** or in a local `.env` file:

```
NOTION_TOKEN=<your_notion_token>
NOTION_API_VERSION=2022-06-28
NOTION_DAILY_DB=<daily_notes_database_id>
NOTION_ZK_DB=<zettelkasten_database_id>
NOTION_HABIT_DB=<habit_database_id>
```

Optional:
```
NOTION_DATABASE_ID=<default_database_id>
NOTION_DATA_SOURCE_ID=<data_source_id_for_new_API>
```

---

## Agent Integration

Once deployed, connect your MCP endpoint to **OpenAI Agent Builder**:

1. Add a **Remote MCP** node.  
2. Set the URL to your Cloud endpoint (e.g. `https://kas-notion.fastmcp.app/mcp`).  
3. Connect it to your main agent logic node.  
4. Grant tool access to your Notion functions.

Your agent can now classify, log, and query notes directly in Notion through this MCP.

---

## Local Testing

You can test your MCP locally before deployment using the `Client` interface:

```python
from fastmcp import Client
import asyncio

URL = "https://kas-notion.fastmcp.app/mcp"

async def main():
    async with Client(URL) as c:
        print(await c.list_tools())
        res = await c.call_tool("notion_query_database", {"page_size": 2})
        print(res)

asyncio.run(main())
```

---

## Learn More

- [FastMCP Documentation](https://gofastmcp.com)  
- [FastMCP Cloud](https://fastmcp.cloud)  
- [MCP Protocol](https://modelcontextprotocol.io)  

---

*This repository was created and customized from the FastMCP quickstart template.*

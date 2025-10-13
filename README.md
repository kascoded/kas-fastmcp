# 🧠 Kas FastMCP — Notion MCP Server

A modular **FastMCP** (Fast Multi-Connected Platform) server built for **Notion API v2025-09-03** integration.
This project powers AI agents and automation workflows that read, query, and create items in multiple Notion databases and data sources — such as your **Zettelkasten**, **Habits**, and other structured systems.

---

## 📂 Project Structure

```
KAS-FASTMCP/
│
├── .env                        # Environment variables (Notion token, DB IDs)
├── config.py                   # Centralized configuration for tokens & databases
├── main.py                     # Local runner for MCP testing
├── notion_server/
│   ├── server.py               # Initializes FastMCP app & loads tools
│   └── tools/
│       ├── __init__.py
│       └── notion_api.py       # All Notion tool logic (query, get, create)
│
├── pyproject.toml              # Project metadata (optional for FastMCP Cloud)
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
└── .gitignore                  # Standard ignore rules for Python + venv
```

---

## ⚙️ Environment Setup

### 1. Clone the repository

```bash
git clone https://github.com/<yourusername>/kas-fastmcp.git
cd kas-fastmcp
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate     # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file in the project root

```bash
NOTION_TOKEN=secret_xxxxx
NOTION_API_VERSION=2025-09-03

ZETTELKASTEN_DATABASE_ID=xxxxxxxxxxxxxxxx
ZETTELKASTEN_DATA_SOURCE_ID=xxxxxxxxxxxxxxxx
HABIT_DATABASE_ID=xxxxxxxxxxxxxxxx
```

> **Note:** Data sources are new in Notion API 2025-09-03.
> If your database doesn’t use multiple data sources, leave `data_source_id` as `None`.

---

## 🧩 Configuration (`config.py`)

The configuration file loads environment variables and maps all database contexts:

```python
class NotionConfig:
    TOKEN = os.getenv("NOTION_TOKEN")
    API_VERSION = os.getenv("NOTION_API_VERSION", "2025-09-03")

    DATABASES = {
        "zettelkasten": {
            "database_id": os.getenv("ZETTELKASTEN_DATABASE_ID"),
            "data_source_id": os.getenv("ZETTELKASTEN_DATA_SOURCE_ID"),
        },
        "habits": {
            "database_id": os.getenv("HABIT_DATABASE_ID"),
            "data_source_id": None,
        },
    }
```

---

## 🚀 Running Locally

Run your MCP server locally for testing:

```bash
python main.py
```

This starts your **KasNotionMCP** instance and exposes the registered tools (`notion_query`, `notion_get_page`, `notion_create_item`) to connected agents.

---

## 🧠 Core Tools

| Tool                 | Description                                                      | API Endpoint                                                |
| -------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------- |
| `notion_query`       | Query a database or data source (auto-detects new vs legacy API) | `/v1/data_sources/{id}/query` or `/v1/databases/{id}/query` |
| `notion_get_page`    | Retrieve a single Notion page by ID                              | `/v1/pages/{page_id}`                                       |
| `notion_create_item` | Create a new entry in a Notion data source or database           | `/v1/data_sources/{id}/items` or `/v1/pages`                |

---

## 💡 Example Usage

### Query Zettelkasten

```python
notion_query("zettelkasten", page_size=5)
```

### Query Habit Tracker

```python
notion_query("habits", filter={"property": "Done", "checkbox": {"equals": False}})
```

### Create a new Zettel

```python
notion_create_item(
    "zettelkasten",
    properties={
        "Title": {"title": [{"text": {"content": "AI Philosophy Notes"}}]},
        "Tags": {"multi_select": [{"name": "Systems"}]},
    }
)
```

---

## 🧱 Built With

* [FastMCP](https://github.com/jlowin/fastmcp) — lightweight multi-client Python framework
* [Notion API v2025-09-03](https://developers.notion.com/reference/intro) — updated with Data Source support
* [httpx](https://www.python-httpx.org/) — async-ready HTTP client
* [python-dotenv](https://pypi.org/project/python-dotenv/) — for secure local config loading

---

## 🧭 Future Additions

* [ ] `notion_update_item()` — update existing pages/items
* [ ] Logging and error tracing middleware
* [ ] Expand to support Obsidian and Flowise data integrations
* [ ] Dockerfile for deployment
* [ ] MCP Cloud deployment instructions

---

## 🪶 License

MIT License © 2025 **Kas Creative Group**

---

## 🧰 Author

**Miras Kasymkhan**
🎨 [miraskas.com](https://miraskas.com)
🧩 [kascurated.com](https://kascurated.com)
🧠 Creator of the *Kas Digital Systems* and *KasOS* ecosystem.

import os
from dotenv import load_dotenv

load_dotenv()

class NotionConfig:
    TOKEN = os.getenv("NOTION_TOKEN")
    API_VERSION = os.getenv("NOTION_API_VERSION", "2022-06-28")

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
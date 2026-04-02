"""
Schema Manager
Handles fetching and caching Notion database schemas.
No state mutation - returns new objects.
"""

import asyncio
import time
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from config import NotionConfig

logger = logging.getLogger(__name__)

_SCHEMA_TTL = 3600  # seconds before a cached schema is considered stale
_CACHE_DIR = Path.home() / ".cache" / "kas-fastmcp"
_CACHE_FILE = _CACHE_DIR / "schema_cache.json"


class SchemaManager:
    """Manages database schemas and data source resolution with disk persistence."""

    def __init__(self, client):
        """
        Initialize schema manager.

        Args:
            client: NotionClient instance
        """
        self.client = client
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
        self._schema_cache_time: Dict[str, float] = {}
        self._raw_cache: Dict[str, Dict[str, Any]] = {}  # Full data_source API response
        self._data_source_cache: Dict[str, str] = {}
        self._schema_locks: Dict[str, asyncio.Lock] = {}
        self._ds_locks: Dict[str, asyncio.Lock] = {}
        
        # Load cache from disk if available
        self._load_from_disk()

    def _load_from_disk(self):
        """Load cached data from disk."""
        if not _CACHE_FILE.exists():
            return

        try:
            with open(_CACHE_FILE, "r") as f:
                data = json.load(f)
                self._schema_cache = data.get("schemas", {})
                self._data_source_cache = data.get("data_source_ids", {})
                # We use real time for the TTL, but since we restarted, 
                # we'll mark them as "just fetched" or let them expire naturally.
                # For safety, we'll mark them as fetched 'now' but they will expire in 1h.
                now = time.monotonic()
                for source in self._schema_cache:
                    self._schema_cache_time[source] = now
            logger.info("Loaded schema cache from %s", _CACHE_FILE)
        except Exception as e:
            logger.warning("Failed to load schema cache: %s", e)

    def _save_to_disk(self):
        """Save current cache to disk."""
        try:
            _CACHE_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "schemas": self._schema_cache,
                "data_source_ids": self._data_source_cache,
                "updated_at": time.time()
            }
            # Write to temp file then move for atomicity
            tmp_file = _CACHE_FILE.with_suffix(".tmp")
            with open(tmp_file, "w") as f:
                json.dump(data, f, indent=2)
            tmp_file.replace(_CACHE_FILE)
        except Exception as e:
            logger.error("Failed to save schema cache: %s", e)

    def _schema_lock(self, source_name: str) -> asyncio.Lock:
        if source_name not in self._schema_locks:
            self._schema_locks[source_name] = asyncio.Lock()
        return self._schema_locks[source_name]

    def _ds_lock(self, source_name: str) -> asyncio.Lock:
        if source_name not in self._ds_locks:
            self._ds_locks[source_name] = asyncio.Lock()
        return self._ds_locks[source_name]
    
    def get_source_config(self, source_name: str) -> Dict[str, Any]:
        """
        Get source configuration from NotionConfig.
        
        Args:
            source_name: Name of the data source
            
        Returns:
            Source configuration dict
            
        Raises:
            ValueError: If source not found in config
        """
        source = NotionConfig.DATABASES.get(source_name)
        if not source:
            available = list(NotionConfig.DATABASES.keys())
            raise ValueError(
                f"Unknown source '{source_name}'. "
                f"Available: {available}"
            )
        
        if not source.get("database_id") and not source.get("data_source_id"):
            raise ValueError(
                f"Source '{source_name}' missing both database_id and data_source_id"
            )
        
        return source.copy()  # Return copy to prevent mutation
    
    async def get_data_source_id(self, source_name: str) -> str:
        """
        Get data source ID for a source.
        Fetches from API if not in config, caches result in memory (not in config).
        
        Args:
            source_name: Name of the data source
            
        Returns:
            Data source ID
        """
        # Fast path — no lock needed for a cache hit
        if source_name in self._data_source_cache:
            return self._data_source_cache[source_name]

        async with self._ds_lock(source_name):
            # Re-check after acquiring lock (another coroutine may have populated it)
            if source_name in self._data_source_cache:
                return self._data_source_cache[source_name]

            source = self.get_source_config(source_name)

            # If already in config, use it
            if source.get("data_source_id"):
                ds_id = source["data_source_id"]
                self._data_source_cache[source_name] = ds_id
                return ds_id

            # Fetch from API
            database_id = source.get("database_id")
            if not database_id:
                raise ValueError(
                    f"Cannot resolve data_source_id for '{source_name}': "
                    f"no database_id available"
                )

            db_json = await self.client.get(f"databases/{database_id}")
            data_sources = db_json.get("data_sources", [])

            if not data_sources:
                raise RuntimeError(
                    f"Database '{source_name}' has no data sources. "
                    f"In Notion: Settings → Manage data sources → Copy data source ID"
                )

            ds_id = data_sources[0].get("id")
            if not ds_id:
                raise RuntimeError("Data source missing ID in API response")

            self._data_source_cache[source_name] = ds_id
            self._save_to_disk()
            return ds_id
    
    async def get_schema(self, source_name: str) -> Dict[str, Any]:
        """
        Fetch database schema (properties) from Notion API.
        Caches result to avoid repeated API calls.
        
        Args:
            source_name: Name of the data source
            
        Returns:
            Properties schema dict
        """
        # Fast path — valid cache hit, no lock needed
        if source_name in self._schema_cache:
            if time.monotonic() - self._schema_cache_time[source_name] < _SCHEMA_TTL:
                return self._schema_cache[source_name]

        async with self._schema_lock(source_name):
            # Re-check after acquiring lock (another coroutine may have fetched already)
            if source_name in self._schema_cache:
                if time.monotonic() - self._schema_cache_time[source_name] < _SCHEMA_TTL:
                    return self._schema_cache[source_name]

            # Fetch from API
            data_source_id = await self.get_data_source_id(source_name)
            result = await self.client.get(f"data_sources/{data_source_id}")
            self._raw_cache[source_name] = result

            # Extract and format schema
            properties = result.get("properties", {})
            schema = {}

            for key, prop in properties.items():
                schema[key] = {
                    "type": prop.get("type"),
                    "id": prop.get("id"),
                }

                if prop.get("type") == "select":
                    options = prop.get("select", {}).get("options", [])
                    schema[key]["options"] = [opt.get("name") for opt in options]

                elif prop.get("type") == "multi_select":
                    options = prop.get("multi_select", {}).get("options", [])
                    schema[key]["options"] = [opt.get("name") for opt in options]

                elif prop.get("type") == "status":
                    options = prop.get("status", {}).get("options", [])
                    schema[key]["options"] = [opt.get("name") for opt in options]

            self._schema_cache[source_name] = schema
            self._schema_cache_time[source_name] = time.monotonic()
            self._save_to_disk()
            return schema

    async def get_data_source_info(self, source_name: str) -> Dict[str, Any]:
        """
        Return the full data_source API response for a source.
        Uses the raw cache populated by get_schema; fetches if not cached.
        """
        if source_name not in self._raw_cache:
            await self.get_schema(source_name)
        return self._raw_cache[source_name]

    def clear_cache(self, source_name: Optional[str] = None):
        """
        Clear cached schemas and data source IDs.

        Args:
            source_name: Specific source to clear, or None for all
        """
        if source_name:
            self._schema_cache.pop(source_name, None)
            self._schema_cache_time.pop(source_name, None)
            self._raw_cache.pop(source_name, None)
            self._data_source_cache.pop(source_name, None)
            # Keep locks — they're reusable and cheap
        else:
            self._schema_cache.clear()
            self._schema_cache_time.clear()
            self._raw_cache.clear()
            self._data_source_cache.clear()

        self._save_to_disk()
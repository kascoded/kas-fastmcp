"""
Schema Manager
Handles fetching and caching Notion database schemas.
No state mutation - returns new objects.
"""

from typing import Dict, Any, Optional
from config import NotionConfig


class SchemaManager:
    """Manages database schemas and data source resolution."""
    
    def __init__(self, client):
        """
        Initialize schema manager.
        
        Args:
            client: NotionClient instance
        """
        self.client = client
        self._schema_cache: Dict[str, Dict[str, Any]] = {}
        self._data_source_cache: Dict[str, str] = {}
    
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
        # Check cache first
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
        
        # Get database to find data sources
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
        
        # Cache it (in memory only, not in config)
        self._data_source_cache[source_name] = ds_id
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
        # Check cache
        if source_name in self._schema_cache:
            return self._schema_cache[source_name]
        
        # Fetch from API
        data_source_id = await self.get_data_source_id(source_name)
        result = await self.client.get(f"data_sources/{data_source_id}")
        
        # Extract and format schema
        properties = result.get("properties", {})
        schema = {}
        
        for key, prop in properties.items():
            schema[key] = {
                "type": prop.get("type"),
                "id": prop.get("id"),
            }
            
            # Add type-specific details
            if prop.get("type") == "select":
                options = prop.get("select", {}).get("options", [])
                schema[key]["options"] = [opt.get("name") for opt in options]
                
            elif prop.get("type") == "multi_select":
                options = prop.get("multi_select", {}).get("options", [])
                schema[key]["options"] = [opt.get("name") for opt in options]
                
            elif prop.get("type") == "status":
                options = prop.get("status", {}).get("options", [])
                schema[key]["options"] = [opt.get("name") for opt in options]
        
        # Cache it
        self._schema_cache[source_name] = schema
        return schema
    
    def clear_cache(self, source_name: Optional[str] = None):
        """
        Clear cached schemas and data source IDs.
        
        Args:
            source_name: Specific source to clear, or None for all
        """
        if source_name:
            self._schema_cache.pop(source_name, None)
            self._data_source_cache.pop(source_name, None)
        else:
            self._schema_cache.clear()
            self._data_source_cache.clear()
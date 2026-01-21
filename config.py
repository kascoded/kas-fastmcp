"""
Notion Configuration Module
Loads configuration from databases.yaml and environment variables.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _load_databases_from_yaml() -> Dict[str, Dict[str, Any]]:
    """
    Load database configuration from databases.yaml.
    
    Returns:
        Dictionary of database configurations
        
    Raises:
        FileNotFoundError: If databases.yaml doesn't exist
        ValueError: If YAML is invalid or empty
    """
    yaml_path = Path(__file__).parent / "databases.yaml"
    
    if not yaml_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {yaml_path}\n"
            f"Create databases.yaml with your database configurations.\n"
            f"See databases.yaml.example for template."
        )
    
    try:
        with open(yaml_path, "r") as f:
            databases = yaml.safe_load(f) or {}
            
        # Filter out None values and comments
        databases = {k: v for k, v in databases.items() if v and isinstance(v, dict)}
        
        if not databases:
            raise ValueError(
                "databases.yaml is empty or contains no valid database entries.\n"
                "Add at least one database configuration."
            )
            
        return databases
        
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in databases.yaml: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to load databases.yaml: {e}")


class NotionConfig:
    """
    Notion API configuration.
    
    Configuration is loaded from:
    1. Environment variables (TOKEN, API_VERSION)
    2. databases.yaml (database configurations)
    """
    
    TOKEN = os.getenv("NOTION_TOKEN")
    API_VERSION = os.getenv("NOTION_API_VERSION", "2025-09-03")
    
    # Load databases from YAML only (no hardcoded fallback)
    try:
        DATABASES = _load_databases_from_yaml()
    except (FileNotFoundError, ValueError) as e:
        # Re-raise with helpful error message
        raise RuntimeError(
            f"Configuration Error: {e}\n\n"
            f"To fix this:\n"
            f"1. Create databases.yaml in the project root\n"
            f"2. Add your database configurations\n"
            f"3. See databases.yaml.example for reference"
        ) from e
    
    @classmethod
    def validate(cls):
        """
        Validate configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        errors = []
        
        # Validate token
        if not cls.TOKEN:
            errors.append(
                "NOTION_TOKEN is required. Set it in your .env file:\n"
                "  NOTION_TOKEN=ntn_your_token_here"
            )
        elif not (cls.TOKEN.startswith("secret_") or cls.TOKEN.startswith("ntn_")):
            errors.append(
                "NOTION_TOKEN has invalid format.\n"
                "Expected: 'ntn_...' (new) or 'secret_...' (legacy)"
            )
        
        # Validate databases
        if not cls.DATABASES:
            errors.append("No databases configured in databases.yaml")
        
        for name, db in cls.DATABASES.items():
            # Check for required fields
            if not db.get("database_id") and not db.get("data_source_id"):
                errors.append(
                    f"Database '{name}' is missing both database_id and data_source_id.\n"
                    f"Provide at least one of these in databases.yaml"
                )
        
        if errors:
            raise ValueError(
                "Configuration Errors:\n" + 
                "\n".join(f"  • {e}" for e in errors)
            )
        
        return True
    
    @classmethod
    def get_database_config(cls, name: str) -> Dict[str, Any]:
        """
        Get full database configuration by name.
        
        Args:
            name: Database name from databases.yaml
            
        Returns:
            Database configuration dict
            
        Raises:
            ValueError: If database not found
        """
        db = cls.DATABASES.get(name)
        if not db:
            available = list(cls.DATABASES.keys())
            raise ValueError(
                f"Database '{name}' not found in configuration.\n"
                f"Available databases: {available}"
            )
        return db.copy()  # Return copy to prevent mutation
    
    @classmethod
    def get_database_id(cls, name: str) -> Optional[str]:
        """Get database ID by name (may be None)."""
        db = cls.get_database_config(name)
        return db.get("database_id")
    
    @classmethod
    def get_data_source_id(cls, name: str) -> Optional[str]:
        """Get data source ID by name (may be None)."""
        db = cls.get_database_config(name)
        return db.get("data_source_id")
    
    @classmethod
    def get_title_property(cls, name: str) -> str:
        """
        Get title property name for a database.
        Defaults to 'title' if not specified.
        
        Args:
            name: Database name
            
        Returns:
            Title property name
        """
        db = cls.get_database_config(name)
        return db.get("title_property", "title")
    
    @classmethod
    def get_description(cls, name: str) -> Optional[str]:
        """Get database description."""
        db = cls.get_database_config(name)
        return db.get("description")
    
    @classmethod
    def list_databases(cls) -> list[str]:
        """List all configured database names."""
        return list(cls.DATABASES.keys())
    
    @classmethod
    def has_schema(cls, name: str) -> bool:
        """Check if a database has a schema defined in config."""
        db = cls.get_database_config(name)
        schema = db.get("schema")
        return schema is not None and len(schema) > 0
    
    @classmethod
    def get_schema(cls, name: str) -> Optional[Dict[str, Any]]:
        """
        Get hardcoded schema from config.
        Returns None if no schema is defined (schema should be fetched dynamically).
        
        Note: This is for backward compatibility. In Phase 3, we'll prefer
        dynamically fetched schemas from the Notion API.
        """
        db = cls.get_database_config(name)
        return db.get("schema")
    
    @classmethod
    def reload(cls):
        """
        Reload configuration from files.
        Useful for testing or dynamic config updates.
        """
        load_dotenv(override=True)
        cls.TOKEN = os.getenv("NOTION_TOKEN")
        cls.API_VERSION = os.getenv("NOTION_API_VERSION", "2025-09-03")
        cls.DATABASES = _load_databases_from_yaml()

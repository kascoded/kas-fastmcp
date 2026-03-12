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


def _user_config_yaml_path() -> Path:
    """Return the user-level databases.yaml path: ~/.config/kas-fastmcp/databases.yaml."""
    return Path.home() / ".config" / "kas-fastmcp" / "databases.yaml"


def _load_yaml_from_path(yaml_path: Path) -> Optional[Dict[str, Dict[str, Any]]]:
    """Load and parse a databases.yaml file from the given path."""
    if not yaml_path.exists():
        return None

    try:
        with open(yaml_path, "r") as f:
            databases = yaml.safe_load(f) or {}

        # Filter out None values and comments
        databases = {k: v for k, v in databases.items() if v and isinstance(v, dict)}

        return databases if databases else None

    except yaml.YAMLError as e:
        print(f"Warning: Invalid YAML in {yaml_path}: {e}")
        return None
    except Exception as e:
        print(f"Warning: Failed to load {yaml_path}: {e}")
        return None


def _load_databases_from_yaml() -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Load database configuration from databases.yaml.

    Checks in order:
    1. ~/.config/kas-fastmcp/databases.yaml  (user-level, written by notion_sync_schemas)
    2. <project-root>/databases.yaml          (project-local, for development)

    Returns:
        Dictionary of database configurations, or None if neither file exists
    """
    # 1. User-level config takes priority (written by notion_sync_schemas)
    user_path = _user_config_yaml_path()
    result = _load_yaml_from_path(user_path)
    if result is not None:
        return result

    # 2. Fall back to project-local file
    project_path = Path(__file__).parent / "databases.yaml"
    return _load_yaml_from_path(project_path)


def _load_databases_from_env() -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Load database configuration from environment variables.
    Useful for cloud deployments where databases.yaml isn't available.
    
    Expected environment variable format:
        {DATABASE_NAME}_DATA_SOURCE_ID
        {DATABASE_NAME}_DATABASE_ID
        {DATABASE_NAME}_TITLE_PROPERTY (optional)
        {DATABASE_NAME}_DESCRIPTION (optional)
    
    Example:
        ZETTELKASTEN_DATA_SOURCE_ID=1d58645d-6355-8021-8111-000b41f7d430
        ZETTELKASTEN_DATABASE_ID=1d58645d635580cc903acb164bb969b3
        ZETTELKASTEN_TITLE_PROPERTY=title
        ZETTELKASTEN_DESCRIPTION=Personal knowledge management
    
    Returns:
        Dictionary of database configurations, or None if no databases found
    """
    databases = {}
    
    # Find all unique database names from environment variables
    db_names = set()
    for key in os.environ:
        if key.endswith("_DATA_SOURCE_ID") or key.endswith("_DATABASE_ID"):
            # Extract database name (everything before _DATA_SOURCE_ID or _DATABASE_ID)
            if key.endswith("_DATA_SOURCE_ID"):
                db_name = key[:-len("_DATA_SOURCE_ID")].lower()
            else:
                db_name = key[:-len("_DATABASE_ID")].lower()
            db_names.add(db_name)
    
    # Build configuration for each database
    for db_name in db_names:
        prefix = db_name.upper()
        
        data_source_id = os.getenv(f"{prefix}_DATA_SOURCE_ID")
        database_id = os.getenv(f"{prefix}_DATABASE_ID")
        
        # Need at least one ID
        if data_source_id or database_id:
            databases[db_name] = {
                "data_source_id": data_source_id,
                "database_id": database_id,
                "title_property": os.getenv(f"{prefix}_TITLE_PROPERTY", "title"),
                "description": os.getenv(f"{prefix}_DESCRIPTION"),
            }
    
    return databases if databases else None


class NotionConfig:
    """
    Notion API configuration.
    
    Configuration is loaded from (in order of priority):
    1. databases.yaml (local development)
    2. Environment variables (cloud deployment)
    """
    
    TOKEN = os.getenv("NOTION_TOKEN")
    API_VERSION = os.getenv("NOTION_API_VERSION", "2025-09-03")
    
    # Load databases from YAML first, fallback to environment variables
    DATABASES: Dict[str, Dict[str, Any]] = _load_databases_from_yaml() or _load_databases_from_env() or {}
    
    # Track which source was used (for debugging)
    _yaml_result = _load_databases_from_yaml()
    _config_source: str = "yaml" if _yaml_result else ("env" if DATABASES else "none")
    
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
            errors.append(
                "No databases configured. Either:\n"
                "  - Create databases.yaml (local), OR\n"
                "  - Set environment variables (cloud):\n"
                "      ZETTELKASTEN_DATA_SOURCE_ID=your-id\n"
                "      ZETTELKASTEN_DATABASE_ID=your-id"
            )
        
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
                f"Available databases: {available}\n"
                f"Config source: {cls._config_source}"
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
    def get_config_source(cls) -> str:
        """
        Get the source of the database configuration.
        
        Returns:
            'yaml', 'env', or 'none'
        """
        return cls._config_source
    
    @classmethod
    def reload(cls):
        """
        Reload configuration from files and environment.
        Useful for testing or dynamic config updates.
        """
        load_dotenv(override=True)
        cls.TOKEN = os.getenv("NOTION_TOKEN")
        cls.API_VERSION = os.getenv("NOTION_API_VERSION", "2025-09-03")
        cls.DATABASES = _load_databases_from_yaml() or _load_databases_from_env() or {}
        
        # Determine config source
        if _load_databases_from_yaml():
            cls._config_source = "yaml"
        elif cls.DATABASES:
            cls._config_source = "env"
        else:
            cls._config_source = "none"

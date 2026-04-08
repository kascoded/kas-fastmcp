#!/usr/bin/env python3
"""
Notion Assistant MCP Server
Entry point for the FastMCP-based Notion integration.
"""
import logging
import sys
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# Import configuration and validate
from config import NotionConfig

# Validate configuration before starting server
try:
    NotionConfig.validate()
    logger.info("Configuration validated successfully")
    logger.info("Using Notion API version: %s", NotionConfig.API_VERSION)
    logger.info("Configured databases: %s", list(NotionConfig.DATABASES.keys()))
except ValueError as e:
    logger.error("Configuration error:\n%s", e)
    logger.error("Please check your .env file and ensure all required variables are set.")
    sys.exit(1)

# Import and expose the server for FastMCP
# FastMCP's CLI looks for 'mcp', 'server', or 'app' in the module
from notion_server.server import mcp

if __name__ == "__main__":
    logger.info("Starting Notion Assistant MCP Server...")
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception("Server error: %s", e)
        sys.exit(1)
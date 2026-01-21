"""
Notion API HTTP Client
Handles all HTTP communication with Notion API.
No business logic - pure HTTP wrapper.
"""

from typing import Optional, Dict, Any
import httpx
from config import NotionConfig


class NotionClient:
    """Async HTTP client for Notion API."""
    
    def __init__(self, token: Optional[str] = None, api_version: Optional[str] = None):
        """
        Initialize Notion client.
        
        Args:
            token: Notion API token (defaults to NotionConfig.TOKEN)
            api_version: API version (defaults to NotionConfig.API_VERSION)
        """
        self.token = token or self._validate_token(NotionConfig.TOKEN)
        self.api_version = api_version or NotionConfig.API_VERSION or "2025-09-03"
        self.base_url = "https://api.notion.com/v1"
    
    @staticmethod
    def _validate_token(token: Optional[str]) -> str:
        """Validate Notion API token format."""
        if not token:
            raise RuntimeError("Missing NOTION_TOKEN in environment or config.")
        
        token = token.strip()
        if not (token.startswith("ntn_") or token.startswith("secret_")):
            raise RuntimeError(
                "Invalid Notion API token format. "
                "Expected format: 'ntn_...' (new) or 'secret_...' (legacy)"
            )
        return token
    
    def _headers(self) -> Dict[str, str]:
        """Build request headers."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.api_version,
            "Content-Type": "application/json",
        }
    
    async def request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: int = 45,
    ) -> Dict[str, Any]:
        """
        Make async HTTP request to Notion API.
        
        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            endpoint: API endpoint (without base URL)
            payload: Request body (for POST/PATCH)
            timeout: Request timeout in seconds
            
        Returns:
            JSON response from Notion API
            
        Raises:
            RuntimeError: On HTTP errors with helpful messages
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                error_body = e.response.text
                
                # Provide actionable error messages
                if status == 401:
                    raise RuntimeError(
                        f"Authentication failed (401).\n"
                        f"Verify:\n"
                        f"  1. Token is valid\n"
                        f"  2. Integration has access to the resource\n"
                        f"Error: {error_body}"
                    )
                elif status == 404:
                    raise RuntimeError(
                        f"Resource not found (404).\n"
                        f"Check:\n"
                        f"  1. Database/page ID is correct\n"
                        f"  2. Integration has access\n"
                        f"Error: {error_body}"
                    )
                elif status == 400:
                    raise RuntimeError(
                        f"Invalid request (400).\n"
                        f"Check request parameters.\n"
                        f"Error: {error_body}"
                    )
                elif status == 429:
                    raise RuntimeError(
                        f"Rate limit exceeded (429).\n"
                        f"Wait before retrying.\n"
                        f"Error: {error_body}"
                    )
                else:
                    raise RuntimeError(f"Notion API error ({status}): {error_body}")
                    
            except httpx.TimeoutException:
                raise RuntimeError(f"Request timed out after {timeout}s")
                
            except Exception as e:
                raise RuntimeError(f"Request failed: {str(e)}")
    
    # Convenience methods for common operations
    
    async def get(self, endpoint: str, timeout: int = 45) -> Dict[str, Any]:
        """GET request."""
        return await self.request("GET", endpoint, timeout=timeout)
    
    async def post(
        self, 
        endpoint: str, 
        payload: Dict[str, Any], 
        timeout: int = 45
    ) -> Dict[str, Any]:
        """POST request."""
        return await self.request("POST", endpoint, payload, timeout)
    
    async def patch(
        self, 
        endpoint: str, 
        payload: Dict[str, Any], 
        timeout: int = 45
    ) -> Dict[str, Any]:
        """PATCH request."""
        return await self.request("PATCH", endpoint, payload, timeout)
    
    async def delete(self, endpoint: str, timeout: int = 45) -> Dict[str, Any]:
        """DELETE request."""
        return await self.request("DELETE", endpoint, timeout=timeout)
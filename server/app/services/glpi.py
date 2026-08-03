"""GLPI API client service."""

import httpx
import logging
from typing import Optional, Dict, Any, List
from config import settings

logger = logging.getLogger(__name__)


class GLPIClient:
    """Client for GLPI API REST."""
    
    def __init__(self):
        self.base_url = settings.GLPI_BASE_URL
        self.app_token = settings.GLPI_APP_TOKEN
        self.user_token = None
        self.headers = {
            "Content-Type": "application/json",
            "App-Token": self.app_token
        }
    
    async def init_session(self, username: str, password: str) -> bool:
        """Initialize GLPI session and get user token."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/initSession",
                    json={"login_name": username, "login_password": password},
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.user_token = data.get("session_token")
                    self.headers["Session-Token"] = self.user_token
                    logger.info(f"✅ GLPI session initialized for {username}")
                    return True
                else:
                    logger.error(f"❌ GLPI init session failed: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ GLPI connection error: {str(e)}")
            return False
    
    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information from GLPI."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/User/{user_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"❌ Failed to get user info: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"❌ Get user info error: {str(e)}")
            return None
    
    async def search_tickets(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search tickets in GLPI."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/search/Ticket",
                    params={"search": query, "limit": limit},
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", [])
                else:
                    logger.error(f"❌ Ticket search failed: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"❌ Ticket search error: {str(e)}")
            return []
    
    async def get_ticket(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Get ticket details from GLPI."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/Ticket/{ticket_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"❌ Failed to get ticket: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"❌ Get ticket error: {str(e)}")
            return None
    
    async def kill_session(self) -> bool:
        """Close GLPI session."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/killSession",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.user_token = None
                    logger.info("✅ GLPI session closed")
                    return True
                else:
                    return False
        except Exception as e:
            logger.error(f"❌ Kill session error: {str(e)}")
            return False


# Global instance
glpi_client = GLPIClient()

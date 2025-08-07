"""Authentication module for Trio Enterprise API."""

import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from config import settings
import logging

logger = logging.getLogger(__name__)


class TrioAuthManager:
    """Manages authentication with Trio Enterprise API."""
    
    def __init__(self):
        self.base_url = settings.trio_api_base_url
        self.username = settings.trio_api_username
        self.password = settings.trio_api_password
        self.token = settings.trio_api_token
        self._auth_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
        self._session: Optional[httpx.AsyncClient] = None
    
    async def get_session(self) -> httpx.AsyncClient:
        """Get authenticated HTTP session."""
        if self._session is None:
            self._session = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
                headers={
                    "Content-Type": "application/json;charset=iso-8859-1",
                    "Accept": "application/json"
                }
            )
        
        # Ensure we have a valid token
        await self._ensure_authenticated()
        
        # Add auth header
        if self._auth_token:
            self._session.headers["Authorization"] = f"Bearer {self._auth_token}"
        
        return self._session
    
    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid authentication token."""
        if self._is_token_valid():
            return
        
        try:
            if self.token:
                # Use provided API token
                self._auth_token = self.token
                self._token_expires = datetime.now() + timedelta(hours=24)
                logger.info("Using provided API token")
            else:
                # Authenticate with username/password
                await self._authenticate_with_credentials()
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    async def _authenticate_with_credentials(self) -> None:
        """Authenticate using username and password."""
        if not self.username or not self.password:
            raise ValueError("Username and password required for authentication")
        
        auth_data = {
            "username": self.username,
            "password": self.password
        }
        
        async with httpx.AsyncClient(
            base_url=self.base_url, 
            timeout=30.0,
            headers={
                "Content-Type": "application/json;charset=iso-8859-1",
                "Accept": "application/json"
            }
        ) as client:
            response = await client.post("/login", json=auth_data)
            response.raise_for_status()
            
            auth_response = response.json()
            self._auth_token = auth_response.get("access_token")
            
            if not self._auth_token:
                raise ValueError("No access token received from authentication")
            
            # Set token expiration (default 1 hour if not provided)
            expires_in = auth_response.get("expires_in", 3600)
            self._token_expires = datetime.now() + timedelta(seconds=expires_in)
            
            logger.info("Successfully authenticated with Trio Enterprise API")
    
    def _is_token_valid(self) -> bool:
        """Check if current token is valid."""
        if not self._auth_token or not self._token_expires:
            return False
        
        # Add 5 minute buffer before expiration
        return datetime.now() < (self._token_expires - timedelta(minutes=5))
    
    async def _handle_redirect(self, response: httpx.Response) -> str:
        """Handle 307 Temporary Redirect for failover scenarios."""
        if response.status_code == 307:
            redirect_url = response.headers.get('Location')
            if redirect_url:
                logger.info(f"Failover redirect detected, switching to: {redirect_url}")
                # Extract base URL from redirect
                from urllib.parse import urlparse
                parsed = urlparse(redirect_url)
                new_base_url = f"{parsed.scheme}://{parsed.netloc}/te/api"
                
                # Update base URL and invalidate current session
                self.base_url = new_base_url
                if self._session:
                    await self._session.aclose()
                    self._session = None
                self._auth_token = None
                self._token_expires = None
                
                return new_base_url
        return self.base_url

    async def test_connection(self) -> bool:
        """Test connection to Trio Enterprise API."""
        try:
            session = await self.get_session()
            # Use API info endpoint instead of health (more appropriate for Trio API)
            response = await session.get("/")
            
            # Handle potential redirect
            if response.status_code == 307:
                await self._handle_redirect(response)
                # Retry with new URL
                session = await self.get_session()
                response = await session.get("/")
            
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            await self._session.aclose()
            self._session = None


# Global auth manager instance
auth_manager = TrioAuthManager()

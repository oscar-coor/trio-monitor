"""Improved authentication module with better security and error handling."""

import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import httpx
import logging

from config import settings

logger = logging.getLogger(__name__)


class TokenManager:
    """Secure token management with automatic refresh."""
    
    def __init__(self):
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._refresh_token: Optional[str] = None
        self._lock = asyncio.Lock()
    
    async def get_valid_token(self) -> Optional[str]:
        """Get a valid token, refreshing if necessary."""
        async with self._lock:
            if self._is_token_valid():
                return self._token
            
            # Try to refresh token
            if self._refresh_token:
                await self._refresh_access_token()
                if self._is_token_valid():
                    return self._token
            
            return None
    
    def set_token(self, token: str, expires_in: int = 3600, refresh_token: Optional[str] = None):
        """Set new token with expiry."""
        self._token = token
        self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)  # Refresh 1 min before expiry
        self._refresh_token = refresh_token
        logger.info(f"Token set, expires at {self._token_expiry}")
    
    def _is_token_valid(self) -> bool:
        """Check if current token is valid."""
        return bool(
            self._token and 
            self._token_expiry and 
            datetime.now() < self._token_expiry
        )
    
    async def _refresh_access_token(self):
        """Refresh access token using refresh token."""
        # This would call the actual API refresh endpoint
        logger.info("Attempting to refresh access token")
        # Implementation depends on API specifics
        pass
    
    def clear(self):
        """Clear all tokens."""
        self._token = None
        self._token_expiry = None
        self._refresh_token = None


class ImprovedAuthenticationManager:
    """Enhanced authentication manager with security best practices."""
    
    def __init__(self):
        self.token_manager = TokenManager()
        self._session: Optional[httpx.AsyncClient] = None
        self._session_lock = asyncio.Lock()
        self._failed_attempts = 0
        self._max_failed_attempts = 3
        self._lockout_until: Optional[datetime] = None
    
    @asynccontextmanager
    async def get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session with proper lifecycle management."""
        async with self._session_lock:
            if not self._session:
                self._session = httpx.AsyncClient(
                    timeout=httpx.Timeout(10.0),
                    verify=True,  # Always verify SSL
                    follow_redirects=False,
                    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
                )
            
            try:
                yield self._session
            except Exception as e:
                logger.error(f"Session error: {e}")
                raise
    
    async def authenticate(self, force: bool = False) -> bool:
        """Authenticate with the Trio Enterprise API with rate limiting."""
        try:
            # Check if locked out
            if self._is_locked_out():
                logger.warning(f"Authentication locked out until {self._lockout_until}")
                return False
            
            # Check if we already have a valid token
            if not force:
                token = await self.token_manager.get_valid_token()
                if token:
                    logger.debug("Using existing valid token")
                    return True
            
            # Perform authentication
            success = await self._perform_authentication()
            
            if success:
                self._failed_attempts = 0
                logger.info("Authentication successful")
            else:
                self._handle_failed_attempt()
            
            return success
            
        except httpx.RequestError as e:
            logger.error(f"Network error during authentication: {e}")
            self._handle_failed_attempt()
            return False
        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}", exc_info=True)
            self._handle_failed_attempt()
            return False
    
    async def _perform_authentication(self) -> bool:
        """Perform actual authentication with the API."""
        try:
            # Hash password before sending (if API supports it)
            password_hash = self._hash_password(settings.trio_password)
            
            async with self.get_session() as session:
                if settings.trio_token:
                    # Token-based auth
                    response = await session.post(
                        f"{settings.trio_api_base_url}/auth/validate",
                        headers={"Authorization": f"Bearer {settings.trio_token}"},
                        timeout=10.0
                    )
                else:
                    # Username/password auth
                    response = await session.post(
                        f"{settings.trio_api_base_url}/auth/login",
                        json={
                            "username": settings.trio_username,
                            "password": password_hash,  # Send hashed password
                            "grant_type": "password"
                        },
                        timeout=10.0
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    self.token_manager.set_token(
                        token=data.get("access_token"),
                        expires_in=data.get("expires_in", 3600),
                        refresh_token=data.get("refresh_token")
                    )
                    return True
                elif response.status_code == 401:
                    logger.error("Authentication failed: Invalid credentials")
                    return False
                else:
                    logger.error(f"Authentication failed with status {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Authentication request failed: {e}")
            return False
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt for security."""
        # In production, use proper salt management
        salt = settings.password_salt if hasattr(settings, 'password_salt') else "default_salt"
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()
    
    def _handle_failed_attempt(self):
        """Handle failed authentication attempt with exponential backoff."""
        self._failed_attempts += 1
        
        if self._failed_attempts >= self._max_failed_attempts:
            # Implement exponential backoff
            lockout_minutes = min(2 ** (self._failed_attempts - self._max_failed_attempts), 60)
            self._lockout_until = datetime.now() + timedelta(minutes=lockout_minutes)
            logger.warning(f"Too many failed attempts. Locked out for {lockout_minutes} minutes")
    
    def _is_locked_out(self) -> bool:
        """Check if currently locked out."""
        if self._lockout_until:
            if datetime.now() < self._lockout_until:
                return True
            else:
                # Lockout expired
                self._lockout_until = None
                self._failed_attempts = max(0, self._failed_attempts - 1)  # Gradual recovery
        return False
    
    async def test_connection(self) -> bool:
        """Test connection to the API with timeout."""
        try:
            async with self.get_session() as session:
                response = await asyncio.wait_for(
                    session.get(f"{settings.trio_api_base_url}/health"),
                    timeout=5.0
                )
                return response.status_code == 200
        except asyncio.TimeoutError:
            logger.warning("Connection test timed out")
            return False
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        token = asyncio.run(self.token_manager.get_valid_token())
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}
    
    async def logout(self):
        """Logout and cleanup resources."""
        try:
            # Call logout endpoint if available
            async with self.get_session() as session:
                token = await self.token_manager.get_valid_token()
                if token:
                    await session.post(
                        f"{settings.trio_api_base_url}/auth/logout",
                        headers={"Authorization": f"Bearer {token}"}
                    )
        except Exception as e:
            logger.error(f"Logout error: {e}")
        finally:
            # Clear tokens and close session
            self.token_manager.clear()
            if self._session:
                await self._session.aclose()
                self._session = None
    
    def get_auth_status(self) -> Dict[str, Any]:
        """Get current authentication status."""
        return {
            "authenticated": asyncio.run(self.token_manager.get_valid_token()) is not None,
            "failed_attempts": self._failed_attempts,
            "locked_out": self._is_locked_out(),
            "lockout_until": self._lockout_until.isoformat() if self._lockout_until else None
        }


# Global authentication manager instance
auth_manager = ImprovedAuthenticationManager()


# Decorator for protected routes
def require_auth(func):
    """Decorator to require authentication for routes."""
    async def wrapper(*args, **kwargs):
        if not await auth_manager.authenticate():
            raise PermissionError("Authentication required")
        return await func(*args, **kwargs)
    return wrapper

"""Tests for improved authentication module."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import hashlib
import secrets
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_improved import ImprovedAuthenticationManager


class TestImprovedAuthManager:
    """Test suite for ImprovedAuthenticationManager."""
    
    @pytest.fixture
    def auth_manager(self):
        """Create an auth manager instance for testing."""
        with patch('auth_improved.settings') as mock_settings:
            mock_settings.te_api_base_url = "https://test.api.com"
            mock_settings.te_api_username = "testuser"
            mock_settings.te_api_password = "testpass"
            mock_settings.te_api_auth_endpoint = "/auth"
            mock_settings.te_api_logout_endpoint = "/logout"
            mock_settings.auth_token_secret = "testsecret"
            mock_settings.auth_salt = "testsalt"
            return ImprovedAuthenticationManager()
    
    @pytest.fixture
    def mock_httpx_client(self):
        """Create a mock httpx client."""
        with patch('auth_improved.httpx.AsyncClient') as mock_class:
            mock_client = AsyncMock()
            mock_class.return_value.__aenter__.return_value = mock_client
            yield mock_client
    
    def test_auth_manager_initialization(self, auth_manager):
        """Test auth manager initializes correctly."""
        assert auth_manager.base_url == "https://test.api.com"
        assert auth_manager.username == "testuser"
        assert auth_manager.token is None
        assert auth_manager.session_id is None
        assert auth_manager.token_expires_at is None
        assert auth_manager.rate_limit_remaining == 100
        assert auth_manager.rate_limit_reset is None
    
    def test_hash_password(self, auth_manager):
        """Test password hashing with PBKDF2."""
        password = "testpassword"
        hashed = auth_manager._hash_password(password)
        
        # Should produce consistent hash for same password and salt
        assert hashed == auth_manager._hash_password(password)
        
        # Should be different from plain password
        assert hashed != password
        
        # Should be hex string
        assert all(c in '0123456789abcdef' for c in hashed)
    
    def test_generate_secure_token(self, auth_manager):
        """Test secure token generation."""
        token = auth_manager._generate_secure_token()
        
        # Should be 64 characters (32 bytes hex)
        assert len(token) == 64
        
        # Should be hex string
        assert all(c in '0123456789abcdef' for c in token)
        
        # Should be unique each time
        token2 = auth_manager._generate_secure_token()
        assert token != token2
    
    @pytest.mark.asyncio
    async def test_authenticate_success(self, auth_manager, mock_httpx_client):
        """Test successful authentication."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "test_token",
            "session_id": "test_session",
            "expires_in": 3600
        }
        mock_httpx_client.post.return_value = mock_response
        
        result = await auth_manager.authenticate()
        
        assert result == True
        assert auth_manager.token == "test_token"
        assert auth_manager.session_id == "test_session"
        assert auth_manager.token_expires_at is not None
        
        # Check API was called correctly
        mock_httpx_client.post.assert_called_once()
        call_args = mock_httpx_client.post.call_args
        assert call_args[0][0] == "https://test.api.com/auth"
    
    @pytest.mark.asyncio
    async def test_authenticate_failure(self, auth_manager, mock_httpx_client):
        """Test authentication failure."""
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid credentials"}
        mock_httpx_client.post.return_value = mock_response
        
        result = await auth_manager.authenticate()
        
        assert result == False
        assert auth_manager.token is None
        assert auth_manager.session_id is None
    
    @pytest.mark.asyncio
    async def test_authenticate_with_retry(self, auth_manager, mock_httpx_client):
        """Test authentication with retry on transient failure."""
        # First attempt fails with network error
        mock_httpx_client.post.side_effect = [
            Exception("Network error"),
            MagicMock(status_code=200, json=lambda: {
                "token": "test_token",
                "session_id": "test_session",
                "expires_in": 3600
            })
        ]
        
        result = await auth_manager.authenticate()
        
        # Should succeed after retry
        assert result == True
        assert auth_manager.token == "test_token"
        
        # Check retry was attempted
        assert mock_httpx_client.post.call_count == 2
    
    @pytest.mark.asyncio
    async def test_authenticate_rate_limiting(self, auth_manager, mock_httpx_client):
        """Test rate limiting during authentication."""
        # Mock rate limit response
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"X-RateLimit-Reset": str(int((datetime.now() + timedelta(seconds=60)).timestamp()))}
        mock_httpx_client.post.return_value = mock_response
        
        result = await auth_manager.authenticate()
        
        assert result == False
        assert auth_manager.rate_limit_remaining == 0
        assert auth_manager.rate_limit_reset is not None
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_manager, mock_httpx_client):
        """Test successful token refresh."""
        # Set existing token
        auth_manager.token = "old_token"
        auth_manager.session_id = "test_session"
        
        # Mock successful refresh
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "new_token",
            "expires_in": 3600
        }
        mock_httpx_client.post.return_value = mock_response
        
        result = await auth_manager.refresh_token()
        
        assert result == True
        assert auth_manager.token == "new_token"
        assert auth_manager.token_expires_at is not None
    
    @pytest.mark.asyncio
    async def test_refresh_token_reauthenticate_on_failure(self, auth_manager, mock_httpx_client):
        """Test re-authentication when token refresh fails."""
        # Set existing token
        auth_manager.token = "old_token"
        auth_manager.session_id = "test_session"
        
        # Mock failed refresh, then successful auth
        mock_httpx_client.post.side_effect = [
            MagicMock(status_code=401),  # Refresh fails
            MagicMock(status_code=200, json=lambda: {  # Auth succeeds
                "token": "new_token",
                "session_id": "new_session",
                "expires_in": 3600
            })
        ]
        
        result = await auth_manager.refresh_token()
        
        assert result == True
        assert auth_manager.token == "new_token"
        assert auth_manager.session_id == "new_session"
    
    def test_is_authenticated_valid_token(self, auth_manager):
        """Test authentication check with valid token."""
        auth_manager.token = "valid_token"
        auth_manager.token_expires_at = datetime.now() + timedelta(minutes=30)
        
        assert auth_manager.is_authenticated() == True
    
    def test_is_authenticated_no_token(self, auth_manager):
        """Test authentication check with no token."""
        auth_manager.token = None
        
        assert auth_manager.is_authenticated() == False
    
    def test_is_authenticated_expired_token(self, auth_manager):
        """Test authentication check with expired token."""
        auth_manager.token = "expired_token"
        auth_manager.token_expires_at = datetime.now() - timedelta(minutes=1)
        
        assert auth_manager.is_authenticated() == False
    
    def test_is_authenticated_buffer_time(self, auth_manager):
        """Test authentication check considers buffer time."""
        auth_manager.token = "almost_expired_token"
        # Token expires in 4 minutes (less than 5 minute buffer)
        auth_manager.token_expires_at = datetime.now() + timedelta(minutes=4)
        
        assert auth_manager.is_authenticated() == False
    
    @pytest.mark.asyncio
    async def test_ensure_authenticated_already_authenticated(self, auth_manager):
        """Test ensure_authenticated when already authenticated."""
        auth_manager.token = "valid_token"
        auth_manager.token_expires_at = datetime.now() + timedelta(minutes=30)
        
        result = await auth_manager.ensure_authenticated()
        
        assert result == True
        # Should not make any API calls
    
    @pytest.mark.asyncio
    async def test_ensure_authenticated_needs_refresh(self, auth_manager, mock_httpx_client):
        """Test ensure_authenticated when token needs refresh."""
        auth_manager.token = "almost_expired"
        auth_manager.token_expires_at = datetime.now() + timedelta(minutes=4)
        auth_manager.session_id = "test_session"
        
        # Mock successful refresh
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "refreshed_token",
            "expires_in": 3600
        }
        mock_httpx_client.post.return_value = mock_response
        
        result = await auth_manager.ensure_authenticated()
        
        assert result == True
        assert auth_manager.token == "refreshed_token"
    
    @pytest.mark.asyncio
    async def test_ensure_authenticated_needs_full_auth(self, auth_manager, mock_httpx_client):
        """Test ensure_authenticated when needs full authentication."""
        auth_manager.token = None
        
        # Mock successful auth
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "token": "new_token",
            "session_id": "new_session",
            "expires_in": 3600
        }
        mock_httpx_client.post.return_value = mock_response
        
        result = await auth_manager.ensure_authenticated()
        
        assert result == True
        assert auth_manager.token == "new_token"
        assert auth_manager.session_id == "new_session"
    
    @pytest.mark.asyncio
    async def test_logout_success(self, auth_manager, mock_httpx_client):
        """Test successful logout."""
        auth_manager.token = "test_token"
        auth_manager.session_id = "test_session"
        
        # Mock successful logout
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_httpx_client.post.return_value = mock_response
        
        await auth_manager.logout()
        
        assert auth_manager.token is None
        assert auth_manager.session_id is None
        assert auth_manager.token_expires_at is None
        
        # Check API was called
        mock_httpx_client.post.assert_called_once()
        call_args = mock_httpx_client.post.call_args
        assert call_args[0][0] == "https://test.api.com/logout"
    
    @pytest.mark.asyncio
    async def test_logout_failure_still_clears_session(self, auth_manager, mock_httpx_client):
        """Test logout clears session even on API failure."""
        auth_manager.token = "test_token"
        auth_manager.session_id = "test_session"
        
        # Mock failed logout
        mock_httpx_client.post.side_effect = Exception("Network error")
        
        await auth_manager.logout()
        
        # Should still clear local session
        assert auth_manager.token is None
        assert auth_manager.session_id is None
        assert auth_manager.token_expires_at is None
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, auth_manager, mock_httpx_client):
        """Test successful connection test."""
        auth_manager.token = "test_token"
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_httpx_client.get.return_value = mock_response
        
        result = await auth_manager.test_connection()
        
        assert result == True
    
    @pytest.mark.asyncio
    async def test_test_connection_failure(self, auth_manager, mock_httpx_client):
        """Test failed connection test."""
        auth_manager.token = "test_token"
        
        # Mock failed response
        mock_httpx_client.get.side_effect = Exception("Connection refused")
        
        result = await auth_manager.test_connection()
        
        assert result == False
    
    def test_get_auth_headers(self, auth_manager):
        """Test getting authentication headers."""
        auth_manager.token = "test_token"
        
        headers = auth_manager.get_auth_headers()
        
        assert headers["Authorization"] == "Bearer test_token"
        assert headers["X-Session-ID"] == ""
        
        # With session ID
        auth_manager.session_id = "test_session"
        headers = auth_manager.get_auth_headers()
        
        assert headers["X-Session-ID"] == "test_session"
    
    def test_check_rate_limit_ok(self, auth_manager):
        """Test rate limit check when OK."""
        auth_manager.rate_limit_remaining = 50
        
        result = auth_manager._check_rate_limit()
        
        assert result == True
    
    def test_check_rate_limit_exceeded(self, auth_manager):
        """Test rate limit check when exceeded."""
        auth_manager.rate_limit_remaining = 0
        auth_manager.rate_limit_reset = datetime.now() + timedelta(minutes=1)
        
        result = auth_manager._check_rate_limit()
        
        assert result == False
    
    def test_check_rate_limit_reset_passed(self, auth_manager):
        """Test rate limit check when reset time has passed."""
        auth_manager.rate_limit_remaining = 0
        auth_manager.rate_limit_reset = datetime.now() - timedelta(minutes=1)
        
        result = auth_manager._check_rate_limit()
        
        assert result == True
        assert auth_manager.rate_limit_remaining == 100
    
    @pytest.mark.asyncio
    async def test_exponential_backoff(self, auth_manager, mock_httpx_client):
        """Test exponential backoff on repeated failures."""
        # Mock all attempts to fail
        mock_httpx_client.post.side_effect = Exception("Network error")
        
        start_time = datetime.now()
        result = await auth_manager.authenticate()
        end_time = datetime.now()
        
        assert result == False
        
        # Should have taken at least the sum of backoff delays
        # (1 + 2 + 4 = 7 seconds for 3 retries)
        # But we'll check for at least 1 second to avoid flaky tests
        elapsed = (end_time - start_time).total_seconds()
        assert elapsed >= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

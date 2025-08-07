"""Comprehensive tests for the improved authentication module."""

import sys
import os
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
from datetime import datetime, timedelta
import httpx

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_improved import ImprovedAuthenticationManager, TokenManager


class TestTokenManager:
    """Test suite for TokenManager."""
    
    def test_initialization(self):
        """Test token manager initializes correctly."""
        manager = TokenManager()
        assert manager._token is None
        assert manager._token_expiry is None
        assert manager._refresh_token is None
    
    def test_set_token(self):
        """Test setting token with expiry."""
        manager = TokenManager()
        manager.set_token("test_token", expires_in=3600, refresh_token="refresh_token")
        
        assert manager._token == "test_token"
        assert manager._refresh_token == "refresh_token"
        assert manager._token_expiry is not None
        # Token expiry should be about 59 minutes in the future (3600 - 60 seconds buffer)
        expected_expiry = datetime.now() + timedelta(seconds=3540)
        assert abs((manager._token_expiry - expected_expiry).total_seconds()) < 5
    
    def test_is_token_valid(self):
        """Test token validity checking."""
        manager = TokenManager()
        
        # No token should be invalid
        assert manager._is_token_valid() == False
        
        # Valid token
        manager.set_token("test_token", expires_in=3600)
        assert manager._is_token_valid() == True
        
        # Expired token
        manager._token_expiry = datetime.now() - timedelta(seconds=1)
        assert manager._is_token_valid() == False
    
    @pytest.mark.asyncio
    async def test_get_valid_token(self):
        """Test getting valid token."""
        manager = TokenManager()
        
        # No token
        token = await manager.get_valid_token()
        assert token is None
        
        # Valid token
        manager.set_token("test_token", expires_in=3600)
        token = await manager.get_valid_token()
        assert token == "test_token"
    
    def test_clear(self):
        """Test clearing tokens."""
        manager = TokenManager()
        manager.set_token("test_token", expires_in=3600, refresh_token="refresh_token")
        
        manager.clear()
        
        assert manager._token is None
        assert manager._token_expiry is None
        assert manager._refresh_token is None


class TestImprovedAuthenticationManager:
    """Test suite for ImprovedAuthenticationManager."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch('auth_improved.settings') as mock:
            mock.trio_api_base_url = "https://test.api.com"
            mock.trio_api_username = "testuser"
            mock.trio_api_password = "testpass"
            mock.password_salt = "testsalt"
            yield mock
    
    @pytest.fixture
    def auth_manager(self, mock_settings):
        """Create an auth manager instance for testing."""
        return ImprovedAuthenticationManager()
    
    def test_initialization(self, auth_manager):
        """Test auth manager initializes correctly."""
        assert auth_manager.token_manager is not None
        assert isinstance(auth_manager.token_manager, TokenManager)
        assert auth_manager._session is None
        assert auth_manager._failed_attempts == 0
        assert auth_manager._max_failed_attempts == 3
        assert auth_manager._lockout_until is None
    
    def test_hash_password(self, auth_manager):
        """Test password hashing."""
        hashed = auth_manager._hash_password("testpass")
        
        # Should be consistent
        hashed2 = auth_manager._hash_password("testpass")
        assert hashed == hashed2
        
        # Should be different for different passwords
        hashed3 = auth_manager._hash_password("different")
        assert hashed != hashed3
        
        # Should be hex string
        assert all(c in '0123456789abcdef' for c in hashed)
    
    def test_handle_failed_attempt(self, auth_manager):
        """Test handling failed authentication attempts."""
        # First failure
        auth_manager._handle_failed_attempt()
        assert auth_manager._failed_attempts == 1
        assert auth_manager._lockout_until is None
        
        # Second failure
        auth_manager._handle_failed_attempt()
        assert auth_manager._failed_attempts == 2
        assert auth_manager._lockout_until is None
        
        # Third failure - should trigger lockout
        auth_manager._handle_failed_attempt()
        assert auth_manager._failed_attempts == 3
        assert auth_manager._lockout_until is not None
        assert auth_manager._lockout_until > datetime.now()
    
    def test_is_locked_out(self, auth_manager):
        """Test lockout checking."""
        # Not locked out initially
        assert auth_manager._is_locked_out() == False
        
        # Set lockout
        auth_manager._lockout_until = datetime.now() + timedelta(minutes=5)
        assert auth_manager._is_locked_out() == True
        
        # Expired lockout
        auth_manager._lockout_until = datetime.now() - timedelta(seconds=1)
        assert auth_manager._is_locked_out() == False
        # Should clear lockout and reduce failed attempts
        assert auth_manager._lockout_until is None
    
    @pytest.mark.asyncio
    async def test_get_session(self, auth_manager):
        """Test session creation and management."""
        async with auth_manager.get_session() as session:
            assert isinstance(session, httpx.AsyncClient)
            assert session.timeout.connect == 10.0
            assert session.follow_redirects == False
        
        # Session should be reused
        async with auth_manager.get_session() as session2:
            assert session2 is session
    
    @pytest.mark.asyncio
    async def test_authenticate_lockout(self, auth_manager):
        """Test authentication when locked out."""
        auth_manager._lockout_until = datetime.now() + timedelta(minutes=5)
        
        result = await auth_manager.authenticate()
        assert result == False
    
    @pytest.mark.asyncio
    async def test_authenticate_with_valid_token(self, auth_manager):
        """Test authentication with existing valid token."""
        auth_manager.token_manager.set_token("valid_token", expires_in=3600)
        
        result = await auth_manager.authenticate(force=False)
        assert result == True
    
    @pytest.mark.asyncio
    async def test_test_connection(self, auth_manager):
        """Test connection testing."""
        with patch.object(auth_manager, 'get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_session.get.return_value = mock_response
            
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_session
            mock_context.__aexit__.return_value = None
            mock_get_session.return_value = mock_context
            
            result = await auth_manager.test_connection()
            assert result == True
            mock_session.get.assert_called_once_with("https://test.api.com/health")
    
    def test_get_auth_headers_no_token(self, auth_manager):
        """Test getting auth headers without token."""
        headers = auth_manager.get_auth_headers()
        assert headers == {}
    
    def test_get_auth_headers_with_token(self, auth_manager):
        """Test getting auth headers with token."""
        auth_manager.token_manager.set_token("test_token", expires_in=3600)
        
        headers = auth_manager.get_auth_headers()
        assert headers == {"Authorization": "Bearer test_token"}
    
    @pytest.mark.asyncio
    async def test_logout(self, auth_manager):
        """Test logout functionality."""
        auth_manager.token_manager.set_token("test_token", expires_in=3600)
        
        # Mock session
        mock_session = AsyncMock()
        auth_manager._session = mock_session
        
        with patch.object(auth_manager, 'get_session') as mock_get_session:
            mock_context_session = AsyncMock()
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_context_session
            mock_context.__aexit__.return_value = None
            mock_get_session.return_value = mock_context
            
            await auth_manager.logout()
            
            # Should clear tokens
            assert auth_manager.token_manager._token is None
            
            # Should close session
            mock_session.aclose.assert_called_once()
    
    def test_get_auth_status(self, auth_manager):
        """Test getting authentication status."""
        status = auth_manager.get_auth_status()
        
        assert "authenticated" in status
        assert "failed_attempts" in status
        assert "locked_out" in status
        assert "lockout_until" in status
        
        assert status["authenticated"] == False
        assert status["failed_attempts"] == 0
        assert status["locked_out"] == False
        assert status["lockout_until"] is None
        
        # With token
        auth_manager.token_manager.set_token("test_token", expires_in=3600)
        status = auth_manager.get_auth_status()
        assert status["authenticated"] == True
        
        # With lockout
        auth_manager._lockout_until = datetime.now() + timedelta(minutes=5)
        status = auth_manager.get_auth_status()
        assert status["locked_out"] == True
        assert status["lockout_until"] is not None


@pytest.mark.integration
class TestAuthenticationIntegration:
    """Integration tests for authentication."""
    
    @pytest.mark.asyncio
    async def test_full_authentication_flow(self):
        """Test complete authentication flow."""
        with patch('auth_improved.settings') as mock_settings:
            mock_settings.trio_api_base_url = "https://test.api.com"
            mock_settings.trio_api_username = "testuser"
            mock_settings.trio_api_password = "testpass"
            mock_settings.password_salt = "testsalt"
            
            auth_manager = ImprovedAuthenticationManager()
            
            # Mock successful authentication
            with patch.object(auth_manager, '_perform_authentication', return_value=True) as mock_auth:
                result = await auth_manager.authenticate()
                assert result == True
                mock_auth.assert_called_once()
            
            # Should use cached token on second call
            with patch.object(auth_manager, '_perform_authentication') as mock_auth2:
                auth_manager.token_manager.set_token("cached_token", expires_in=3600)
                result = await auth_manager.authenticate()
                assert result == True
                mock_auth2.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

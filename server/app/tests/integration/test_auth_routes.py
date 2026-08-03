"""Integration tests for authentication routes."""

import pytest
from httpx import AsyncClient
from datetime import datetime
import jwt

from core.security import hash_password, create_access_token


# ============================================
# LOGIN ENDPOINT TESTS
# ============================================

class TestLoginEndpoint:
    """Test POST /api/auth/login endpoint."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, async_client: AsyncClient, user_factory, monkeypatch):
        """Test successful login with valid credentials."""
        # Create a test user
        password = "TestPassword123!"
        user = user_factory(username="testuser", password=password)
        
        # Mock GLPI authentication
        async def mock_init_session(self, username: str, password: str):
            if username == "testuser" and password == "TestPassword123!":
                self.user_token = "mock_token"
                return True
            return False
        
        async def mock_get_user_info(self, user_id: int):
            return {
                "id": 1,
                "email": "testuser@example.com",
                "is_admin": False,
            }
        
        async def mock_kill_session(self):
            return True
        
        # Patch GLPI client
        from services.glpi import glpi_client
        monkeypatch.setattr(glpi_client, "init_session", mock_init_session.__get__(glpi_client))
        monkeypatch.setattr(glpi_client, "get_user_info", mock_get_user_info.__get__(glpi_client))
        monkeypatch.setattr(glpi_client, "kill_session", mock_kill_session.__get__(glpi_client))
        
        # Make login request
        response = await async_client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "TestPassword123!"
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert "user" in data
        assert "tokens" in data
        assert data["tokens"]["token_type"] == "bearer"
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, async_client: AsyncClient, monkeypatch):
        """Test login with invalid credentials."""
        # Mock GLPI authentication failure
        async def mock_init_session(self, username: str, password: str):
            return False
        
        from services.glpi import glpi_client
        monkeypatch.setattr(glpi_client, "init_session", mock_init_session.__get__(glpi_client))
        
        response = await async_client.post(
            "/api/auth/login",
            json={
                "username": "wronguser",
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "INVALID_CREDENTIALS"
    
    @pytest.mark.asyncio
    async def test_login_missing_username(self, async_client: AsyncClient):
        """Test login without username."""
        response = await async_client.post(
            "/api/auth/login",
            json={
                "password": "TestPassword123!"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_login_missing_password(self, async_client: AsyncClient):
        """Test login without password."""
        response = await async_client.post(
            "/api/auth/login",
            json={
                "username": "testuser"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_login_empty_username(self, async_client: AsyncClient):
        """Test login with empty username."""
        response = await async_client.post(
            "/api/auth/login",
            json={
                "username": "",
                "password": "TestPassword123!"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_login_empty_password(self, async_client: AsyncClient):
        """Test login with empty password."""
        response = await async_client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": ""
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_login_username_too_short(self, async_client: AsyncClient):
        """Test login with username too short."""
        response = await async_client.post(
            "/api/auth/login",
            json={
                "username": "ab",
                "password": "TestPassword123!"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_login_password_too_short(self, async_client: AsyncClient):
        """Test login with password too short."""
        response = await async_client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "short"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_login_response_contains_user_info(self, async_client: AsyncClient, user_factory, monkeypatch):
        """Test that login response contains user information."""
        password = "TestPassword123!"
        user = user_factory(username="testuser", password=password)
        
        async def mock_init_session(self, username: str, password: str):
            return username == "testuser" and password == "TestPassword123!"
        
        async def mock_get_user_info(self, user_id: int):
            return {"id": 1, "email": "test@example.com", "is_admin": False}
        
        async def mock_kill_session(self):
            return True
        
        from services.glpi import glpi_client
        monkeypatch.setattr(glpi_client, "init_session", mock_init_session.__get__(glpi_client))
        monkeypatch.setattr(glpi_client, "get_user_info", mock_get_user_info.__get__(glpi_client))
        monkeypatch.setattr(glpi_client, "kill_session", mock_kill_session.__get__(glpi_client))
        
        response = await async_client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "TestPassword123!"}
        )
        
        data = response.json()
        user_data = data["user"]
        
        assert "id" in user_data
        assert "username" in user_data
        assert "email" in user_data
        assert "is_active" in user_data
        assert "is_admin" in user_data
        assert "created_at" in user_data


# ============================================
# REFRESH TOKEN ENDPOINT TESTS
# ============================================

class TestRefreshTokenEndpoint:
    """Test POST /api/auth/refresh endpoint."""
    
    @pytest.mark.asyncio
    async def test_refresh_with_valid_token(self, async_client: AsyncClient, token_factory):
        """Test token refresh with valid refresh token."""
        refresh_token = token_factory(sub="testuser", token_type="refresh")
        
        response = await async_client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    @pytest.mark.asyncio
    async def test_refresh_with_expired_token(self, async_client: AsyncClient, token_factory):
        """Test token refresh with expired token."""
        expired_token = token_factory(
            sub="testuser",
            token_type="refresh",
            is_expired=True
        )
        
        response = await async_client.post(
            "/api/auth/refresh",
            json={"refresh_token": expired_token}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
    
    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token(self, async_client: AsyncClient):
        """Test token refresh with invalid token."""
        response = await async_client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid_token_string"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_refresh_with_access_token(self, async_client: AsyncClient, token_factory):
        """Test that access token cannot be used for refresh."""
        access_token = token_factory(sub="testuser", token_type="access")
        
        response = await async_client.post(
            "/api/auth/refresh",
            json={"refresh_token": access_token}
        )
        
        # Should fail because token type is 'access', not 'refresh'
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_refresh_missing_token(self, async_client: AsyncClient):
        """Test refresh without token."""
        response = await async_client.post(
            "/api/auth/refresh",
            json={}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_refresh_empty_token(self, async_client: AsyncClient):
        """Test refresh with empty token."""
        response = await async_client.post(
            "/api/auth/refresh",
            json={"refresh_token": ""}
        )
        
        assert response.status_code == 422


# ============================================
# LOGOUT ENDPOINT TESTS
# ============================================

class TestLogoutEndpoint:
    """Test POST /api/auth/logout endpoint."""
    
    @pytest.mark.asyncio
    async def test_logout_without_authentication(self, async_client: AsyncClient):
        """Test logout without authentication."""
        response = await async_client.post(
            "/api/auth/logout",
            json={}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_logout_with_authentication(self, authenticated_client: AsyncClient):
        """Test logout with valid authentication."""
        response = await authenticated_client.post(
            "/api/auth/logout",
            json={}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


# ============================================
# GET CURRENT USER TESTS
# ============================================

class TestGetCurrentUserEndpoint:
    """Test GET /api/auth/me endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_me_without_authentication(self, async_client: AsyncClient):
        """Test getting current user without authentication."""
        response = await async_client.get("/api/auth/me")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_me_with_authentication(self, authenticated_client: AsyncClient):
        """Test getting current user with authentication."""
        response = await authenticated_client.get("/api/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "is_active" in data
    
    @pytest.mark.asyncio
    async def test_get_me_with_invalid_token(self, async_client: AsyncClient):
        """Test getting current user with invalid token."""
        async_client.headers.update({"Authorization": "Bearer invalid_token"})
        response = await async_client.get("/api/auth/me")
        
        assert response.status_code == 401


# ============================================
# CHANGE PASSWORD ENDPOINT TESTS
# ============================================

class TestChangePasswordEndpoint:
    """Test POST /api/auth/change-password endpoint."""
    
    @pytest.mark.asyncio
    async def test_change_password_without_authentication(self, async_client: AsyncClient):
        """Test changing password without authentication."""
        response = await async_client.post(
            "/api/auth/change-password",
            json={
                "current_password": "Current123!",
                "new_password": "NewPassword123!",
                "confirm_password": "NewPassword123!"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_change_password_weak_new_password(self, authenticated_client: AsyncClient):
        """Test changing password with weak new password."""
        response = await authenticated_client.post(
            "/api/auth/change-password",
            json={
                "current_password": "TestPassword123!",
                "new_password": "weak",
                "confirm_password": "weak"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_change_password_mismatch(self, authenticated_client: AsyncClient):
        """Test changing password with mismatched passwords."""
        response = await authenticated_client.post(
            "/api/auth/change-password",
            json={
                "current_password": "TestPassword123!",
                "new_password": "NewPassword123!",
                "confirm_password": "DifferentPassword123!"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_change_password_missing_fields(self, authenticated_client: AsyncClient):
        """Test changing password with missing fields."""
        response = await authenticated_client.post(
            "/api/auth/change-password",
            json={
                "current_password": "TestPassword123!"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_change_password_empty_fields(self, authenticated_client: AsyncClient):
        """Test changing password with empty fields."""
        response = await authenticated_client.post(
            "/api/auth/change-password",
            json={
                "current_password": "",
                "new_password": "",
                "confirm_password": ""
            }
        )
        
        assert response.status_code == 422


# ============================================
# ERROR HANDLING TESTS
# ============================================

class TestAuthErrorHandling:
    """Test error handling in auth endpoints."""
    
    @pytest.mark.asyncio
    async def test_login_returns_request_id(self, async_client: AsyncClient, monkeypatch):
        """Test that error responses include request_id."""
        async def mock_init_session(self, username: str, password: str):
            return False
        
        from services.glpi import glpi_client
        monkeypatch.setattr(glpi_client, "init_session", mock_init_session.__get__(glpi_client))
        
        response = await async_client.post(
            "/api/auth/login",
            json={"username": "user", "password": "pass"}
        )
        
        # Should have request_id in headers or response
        assert "X-Request-ID" in response.headers or "request_id" in response.json()
    
    @pytest.mark.asyncio
    async def test_login_invalid_json(self, async_client: AsyncClient):
        """Test login with invalid JSON."""
        response = await async_client.post(
            "/api/auth/login",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code in [400, 422]


# ============================================
# TOKEN VALIDATION TESTS
# ============================================

class TestTokenValidation:
    """Test token validation in responses."""
    
    @pytest.mark.asyncio
    async def test_login_token_is_valid_jwt(self, async_client: AsyncClient, user_factory, monkeypatch, test_settings):
        """Test that login returns valid JWT tokens."""
        password = "TestPassword123!"
        user = user_factory(username="testuser", password=password)
        
        async def mock_init_session(self, username: str, password: str):
            return username == "testuser"
        
        async def mock_get_user_info(self, user_id: int):
            return {"id": 1, "email": "test@example.com"}
        
        async def mock_kill_session(self):
            return True
        
        from services.glpi import glpi_client
        monkeypatch.setattr(glpi_client, "init_session", mock_init_session.__get__(glpi_client))
        monkeypatch.setattr(glpi_client, "get_user_info", mock_get_user_info.__get__(glpi_client))
        monkeypatch.setattr(glpi_client, "kill_session", mock_kill_session.__get__(glpi_client))
        
        response = await async_client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "TestPassword123!"}
        )
        
        data = response.json()
        access_token = data["tokens"]["access_token"]
        
        # Token should be valid JWT
        assert len(access_token.split(".")) == 3
        
        # Should be decodable
        try:
            decoded = jwt.decode(
                access_token,
                test_settings.JWT_SECRET,
                algorithms=[test_settings.JWT_ALGORITHM]
            )
            assert decoded["sub"] == "testuser"
            assert decoded["type"] == "access"
        except jwt.InvalidTokenError:
            pytest.fail("Invalid JWT token returned")
    
    @pytest.mark.asyncio
    async def test_refresh_token_is_valid_jwt(self, async_client: AsyncClient, user_factory, monkeypatch, test_settings):
        """Test that login returns valid refresh JWT token."""
        password = "TestPassword123!"
        user = user_factory(username="testuser", password=password)
        
        async def mock_init_session(self, username: str, password: str):
            return username == "testuser"
        
        async def mock_get_user_info(self, user_id: int):
            return {"id": 1, "email": "test@example.com"}
        
        async def mock_kill_session(self):
            return True
        
        from services.glpi import glpi_client
        monkeypatch.setattr(glpi_client, "init_session", mock_init_session.__get__(glpi_client))
        monkeypatch.setattr(glpi_client, "get_user_info", mock_get_user_info.__get__(glpi_client))
        monkeypatch.setattr(glpi_client, "kill_session", mock_kill_session.__get__(glpi_client))
        
        response = await async_client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "TestPassword123!"}
        )
        
        data = response.json()
        refresh_token = data["tokens"]["refresh_token"]
        
        # Token should be valid JWT
        assert len(refresh_token.split(".")) == 3
        
        # Should be decodable
        try:
            decoded = jwt.decode(
                refresh_token,
                test_settings.JWT_SECRET,
                algorithms=[test_settings.JWT_ALGORITHM]
            )
            assert decoded["sub"] == "testuser"
            assert decoded["type"] == "refresh"
        except jwt.InvalidTokenError:
            pytest.fail("Invalid refresh JWT token returned")


# ============================================
# RATE LIMITING TESTS (BASIC)
# ============================================

class TestAuthRateLimiting:
    """Test rate limiting on auth endpoints."""
    
    @pytest.mark.asyncio
    async def test_multiple_login_attempts(self, async_client: AsyncClient, monkeypatch):
        """Test multiple login attempts."""
        async def mock_init_session(self, username: str, password: str):
            return False
        
        from services.glpi import glpi_client
        monkeypatch.setattr(glpi_client, "init_session", mock_init_session.__get__(glpi_client))
        
        # Make 5 login attempts
        for i in range(5):
            response = await async_client.post(
                "/api/auth/login",
                json={"username": f"user{i}", "password": "password"}
            )
            
            # Should not be blocked (rate limit is 100 req/60s)
            assert response.status_code in [401, 422]

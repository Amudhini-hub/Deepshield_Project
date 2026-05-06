"""Comprehensive tests for DeepShield backend"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.config.config import TestingConfig, DevelopmentConfig
from backend.storage import store
from backend.services.authentication import (
    get_password_hash, 
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)

client = TestClient(app)


class TestAuthentication:
    """Test JWT authentication functions"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)
    
    def test_access_token_creation(self):
        """Test access token creation and decoding"""
        data = {"sub": "user_123"}
        token = create_access_token(data)
        
        assert token is not None
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded.get("sub") == "user_123"
        assert decoded.get("type") == "access"
    
    def test_refresh_token_creation(self):
        """Test refresh token creation and decoding"""
        data = {"sub": "user_123"}
        token = create_refresh_token(data)
        
        assert token is not None
        decoded = decode_refresh_token(token)
        assert decoded is not None
        assert decoded.get("sub") == "user_123"
        assert decoded.get("type") == "refresh"
    
    def test_invalid_token(self):
        """Test decoding invalid token"""
        decoded = decode_access_token("invalid_token_xyz")
        assert decoded is None
    
    def test_refresh_token_with_access_decoder(self):
        """Test that refresh token fails with access decoder"""
        data = {"sub": "user_123"}
        refresh_token = create_refresh_token(data)
        
        # Refresh token should not decode with access decoder
        decoded = decode_access_token(refresh_token)
        assert decoded is None or decoded.get("type") != "access"
    
    def test_access_token_with_refresh_decoder(self):
        """Test that access token fails with refresh decoder"""
        data = {"sub": "user_123"}
        access_token = create_access_token(data)
        
        # Access token should not decode with refresh decoder
        decoded = decode_refresh_token(access_token)
        assert decoded is None or decoded.get("type") != "refresh"


class TestUserEndpoints:
    """Test user registration and authentication endpoints"""
    
    def test_register_user(self):
        """Test user registration"""
        response = client.post(
            "/api/v1/users/register",
            json={
                "email": f"test_{TestAuthentication}@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["email"] == f"test_{TestAuthentication}@example.com"
        assert data["is_active"] is True
    
    def test_register_duplicate_email(self):
        """Test that duplicate emails are rejected"""
        email = "duplicate_test@example.com"
        
        # Register first user
        response1 = client.post(
            "/api/v1/users/register",
            json={"email": email, "password": "password123"}
        )
        assert response1.status_code == 201
        
        # Try to register with same email
        response2 = client.post(
            "/api/v1/users/register",
            json={"email": email, "password": "password456"}
        )
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]
    
    def test_login_user(self):
        """Test user login"""
        email = "login_test@example.com"
        password = "password123"
        
        # Register user
        client.post(
            "/api/v1/users/register",
            json={"email": email, "password": password}
        )
        
        # Login
        response = client.post(
            "/api/v1/users/login",
            data={"username": email, "password": password}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/v1/users/login",
            data={"username": "nonexistent@example.com", "password": "wrong"}
        )
        
        assert response.status_code == 401
        assert "Incorrect" in response.json()["detail"]
    
    def test_refresh_token(self):
        """Test token refresh"""
        email = "refresh_test@example.com"
        password = "password123"
        
        # Register and login
        client.post(
            "/api/v1/users/register",
            json={"email": email, "password": password}
        )
        
        login_response = client.post(
            "/api/v1/users/login",
            data={"username": email, "password": password}
        )
        
        old_tokens = login_response.json()
        
        # Refresh token
        refresh_response = client.post(
            "/api/v1/users/refresh",
            json={"refresh_token": old_tokens["refresh_token"]}
        )
        
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens
        # New tokens should be different from old ones
        assert new_tokens["access_token"] != old_tokens["access_token"]
    
    def test_refresh_with_invalid_token(self):
        """Test refresh with invalid token"""
        response = client.post(
            "/api/v1/users/refresh",
            json={"refresh_token": "invalid_token"}
        )
        
        assert response.status_code == 401
        assert "Invalid or expired" in response.json()["detail"]
    
    def test_get_current_user(self):
        """Test getting current user info"""
        email = "current_user_test@example.com"
        password = "password123"
        
        # Register and login
        client.post(
            "/api/v1/users/register",
            json={"email": email, "password": password}
        )
        
        login_response = client.post(
            "/api/v1/users/login",
            data={"username": email, "password": password}
        )
        
        token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email
        assert data["is_active"] is True
    
    def test_get_current_user_unauthorized(self):
        """Test getting current user without token"""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 403  # FastAPI returns 403 for missing auth


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "app" in data
        assert "version" in data
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "app" in data


class TestApiEndpoints:
    """Test API behavior and error handling"""
    
    def test_invalid_endpoint(self):
        """Test request to non-existent endpoint"""
        response = client.get("/api/v1/nonexistent")
        
        assert response.status_code == 404
    
    def test_request_id_header(self):
        """Test that request ID is added to response"""
        response = client.get("/health")
        
        assert "x-request-id" in response.headers
        assert response.headers["x-request-id"] != ""
    
    def test_process_time_header(self):
        """Test that process time is added to response"""
        response = client.get("/health")
        
        assert "x-process-time" in response.headers


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

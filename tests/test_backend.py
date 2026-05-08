"""Comprehensive Integration Tests for DeepShield Backend"""

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import backend.crud as crud
from backend.config.config import get_config
from backend.database import drop_db, get_db, init_db
from backend.main import app
from backend.services.authentication import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    get_password_hash,
    verify_password,
)

client = TestClient(app)
config = get_config()

# ==================== FIXTURES ====================


@pytest.fixture(scope="function", autouse=True)
def setup_teardown_db():
    """Setup and teardown database for each test"""
    # Initialize fresh database
    init_db()
    yield
    # Cleanup
    drop_db()


@pytest.fixture
def test_user_data():
    """Test user credentials"""
    return {"email": "testuser@example.com", "password": "TestPassword123"}


@pytest.fixture
def test_user_data_invalid_password():
    """Invalid password (no uppercase)"""
    return {"email": "testuser@example.com", "password": "testpassword123"}


# ==================== AUTHENTICATION TESTS ====================


class TestAuthenticationFunctions:
    """Test JWT authentication functions"""

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("WrongPassword123", hashed)

    def test_access_token_creation(self):
        """Test access token creation and decoding"""
        data = {"sub": "1"}
        token = create_access_token(data)

        assert token is not None
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded.get("sub") == "1"
        assert decoded.get("type") == "access"

    def test_refresh_token_creation(self):
        """Test refresh token creation and decoding"""
        data = {"sub": "1"}
        token = create_refresh_token(data)

        assert token is not None
        decoded = decode_refresh_token(token)
        assert decoded is not None
        assert decoded.get("sub") == "1"
        assert decoded.get("type") == "refresh"

    def test_invalid_token(self):
        """Test decoding invalid token"""
        decoded = decode_access_token("invalid_token_xyz")
        assert decoded is None

    def test_token_type_validation(self):
        """Test that token types are validated"""
        data = {"sub": "1"}
        refresh_token = create_refresh_token(data)
        access_token = create_access_token(data)

        # Refresh token should not decode with access decoder
        decoded = decode_access_token(refresh_token)
        assert decoded is None or decoded.get("type") != "access"

        # Access token should not decode with refresh decoder
        decoded = decode_refresh_token(access_token)
        assert decoded is None or decoded.get("type") != "refresh"


class TestUserRegistration:
    """Test user registration endpoint"""

    def test_register_user_success(self, test_user_data):
        """Test successful user registration"""
        response = client.post("/api/v1/users/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_register_user_duplicate_email(self, test_user_data):
        """Test registration with duplicate email"""
        # First registration
        response1 = client.post("/api/v1/users/register", json=test_user_data)
        assert response1.status_code == 201

        # Duplicate registration
        response2 = client.post("/api/v1/users/register", json=test_user_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]

    def test_register_user_invalid_email(self):
        """Test registration with invalid email"""
        response = client.post(
            "/api/v1/users/register",
            json={"email": "invalid-email", "password": "TestPassword123"},
        )
        assert response.status_code == 422

    def test_register_user_weak_password(self):
        """Test registration with weak password"""
        response = client.post(
            "/api/v1/users/register",
            json={"email": "test@example.com", "password": "weak"},
        )
        assert response.status_code == 422

    def test_register_user_password_no_uppercase(self):
        """Test password must have uppercase"""
        response = client.post(
            "/api/v1/users/register",
            json={"email": "test@example.com", "password": "testpassword123"},
        )
        assert response.status_code == 422


class TestUserLogin:
    """Test user login endpoint"""

    def test_login_success(self, test_user_data):
        """Test successful login"""
        # Register first
        client.post("/api/v1/users/register", json=test_user_data)

        # Login
        response = client.post(
            "/api/v1/users/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_login_invalid_credentials(self, test_user_data):
        """Test login with invalid credentials"""
        # Register
        client.post("/api/v1/users/register", json=test_user_data)

        # Login with wrong password
        response = client.post(
            "/api/v1/users/login",
            data={"username": test_user_data["email"], "password": "WrongPassword123"},
        )

        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        """Test login with nonexistent user"""
        response = client.post(
            "/api/v1/users/login",
            data={"username": "nonexistent@example.com", "password": "Password123"},
        )

        assert response.status_code == 401


class TestTokenRefresh:
    """Test token refresh endpoint"""

    def test_refresh_token_success(self, test_user_data):
        """Test successful token refresh"""
        # Register and login
        client.post("/api/v1/users/register", json=test_user_data)
        login_response = client.post(
            "/api/v1/users/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )

        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = client.post(
            "/api/v1/users/refresh", json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self):
        """Test refresh with invalid token"""
        response = client.post(
            "/api/v1/users/refresh", json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == 401


class TestUserProfile:
    """Test user profile endpoints"""

    def test_get_current_user_success(self, test_user_data):
        """Test getting current user profile"""
        # Register and login
        client.post("/api/v1/users/register", json=test_user_data)
        login_response = client.post(
            "/api/v1/users/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )

        access_token = login_response.json()["access_token"]

        # Get user profile
        response = client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["is_active"] is True

    def test_get_current_user_unauthorized(self):
        """Test getting user profile without auth"""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 403

    def test_update_user_profile(self, test_user_data):
        """Test updating user profile"""
        # Register and login
        client.post("/api/v1/users/register", json=test_user_data)
        login_response = client.post(
            "/api/v1/users/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )

        access_token = login_response.json()["access_token"]

        # Update profile
        response = client.put(
            "/api/v1/users/profile",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"email": "newemail@example.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newemail@example.com"


class TestLogout:
    """Test logout endpoint"""

    def test_logout_success(self, test_user_data):
        """Test successful logout"""
        # Register and login
        client.post("/api/v1/users/register", json=test_user_data)
        login_response = client.post(
            "/api/v1/users/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )

        access_token = login_response.json()["access_token"]

        # Logout
        response = client.post(
            "/api/v1/users/logout", headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestHealthCheck:
    """Test health check endpoint"""

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "ml_services" in data


class TestBehavioralBaseline:
    """Test behavioral baseline creation"""

    def test_create_baseline_success(self, test_user_data):
        """Test creating behavioral baseline"""
        # Register and login
        client.post("/api/v1/users/register", json=test_user_data)
        login_response = client.post(
            "/api/v1/users/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )

        access_token = login_response.json()["access_token"]
        user_id = str(1)  # First user

        # Create baseline
        response = client.post(
            "/api/v1/baseline",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "user_id": user_id,
                "events": [
                    {"type": "keystroke", "timestamp": 1000.0, "is_error": False},
                    {"type": "mouse_move", "timestamp": 1010.0, "x": 100.0, "y": 150.0},
                    {"type": "click", "timestamp": 1015.0, "x": 100.0, "y": 150.0},
                    {"type": "keystroke", "timestamp": 1020.0, "is_error": False},
                    {"type": "keystroke", "timestamp": 1025.0, "is_error": False},
                    {"type": "keystroke", "timestamp": 1030.0, "is_error": False},
                ],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == user_id
        assert "confidence" in data


class TestCRUDOperations:
    """Test database CRUD operations"""

    def test_create_user_crud(self):
        """Test creating user via CRUD"""
        from backend.database import SessionLocal

        db = SessionLocal()
        try:
            user = crud.create_user(db, "crud@example.com", "CrudPassword123")
            assert user.id is not None
            assert user.email == "crud@example.com"
            assert user.is_active is True
        finally:
            db.close()

    def test_get_user_by_email_crud(self):
        """Test getting user by email via CRUD"""
        from backend.database import SessionLocal

        db = SessionLocal()
        try:
            # Create user
            crud.create_user(db, "test@example.com", "TestPassword123")

            # Get user
            user = crud.get_user_by_email(db, "test@example.com")
            assert user is not None
            assert user.email == "test@example.com"
        finally:
            db.close()

    def test_update_user_crud(self):
        """Test updating user via CRUD"""
        from backend.database import SessionLocal

        db = SessionLocal()
        try:
            # Create user
            user = crud.create_user(db, "test@example.com", "TestPassword123")
            user_id = user.id

            # Update user
            updated = crud.update_user(db, user_id, email="newemail@example.com")
            assert updated.email == "newemail@example.com"
        finally:
            db.close()

    def test_create_audit_log_crud(self):
        """Test creating audit log via CRUD"""
        from backend.database import SessionLocal

        db = SessionLocal()
        try:
            log = crud.create_audit_log(db, "user_1", "TEST_EVENT", {"test": "data"})
            assert log.user_id == "user_1"
            assert log.event_type == "TEST_EVENT"
        finally:
            db.close()

    def test_register_user(self):
        """Test user registration"""
        response = client.post(
            "/api/v1/users/register",
            json={
                "email": f"test_{self.__class__.__name__}@example.com",
                "password": "Password123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["email"] == f"test_{self.__class__.__name__}@example.com"
        assert data["is_active"] is True

    def test_register_duplicate_email(self):
        """Test that duplicate emails are rejected"""
        email = "duplicate_test@example.com"

        # Register first user
        response1 = client.post(
            "/api/v1/users/register", json={"email": email, "password": "Password123"}
        )
        assert response1.status_code == 201

        # Try to register with same email
        response2 = client.post(
            "/api/v1/users/register", json={"email": email, "password": "Password456"}
        )
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]

    def test_login_user(self):
        """Test user login"""
        email = "login_test@example.com"
        password = "Password123"

        # Register user
        client.post(
            "/api/v1/users/register", json={"email": email, "password": password}
        )

        # Login
        response = client.post(
            "/api/v1/users/login", data={"username": email, "password": password}
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
            data={"username": "nonexistent@example.com", "password": "wrong"},
        )

        assert response.status_code == 401
        assert "Incorrect" in response.json()["detail"]

    def test_refresh_token(self):
        """Test token refresh"""
        email = "refresh_test@example.com"
        password = "Password123"

        # Register and login
        client.post(
            "/api/v1/users/register", json={"email": email, "password": password}
        )

        login_response = client.post(
            "/api/v1/users/login", data={"username": email, "password": password}
        )

        old_tokens = login_response.json()

        # Refresh token
        refresh_response = client.post(
            "/api/v1/users/refresh", json={"refresh_token": old_tokens["refresh_token"]}
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
            "/api/v1/users/refresh", json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == 401
        assert "Invalid or expired" in response.json()["detail"]

    def test_get_current_user(self):
        """Test getting current user info"""
        email = "current_user_test@example.com"
        password = "Password123"

        # Register and login
        client.post(
            "/api/v1/users/register", json={"email": email, "password": password}
        )

        login_response = client.post(
            "/api/v1/users/login", data={"username": email, "password": password}
        )

        token = login_response.json()["access_token"]

        # Get current user
        response = client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
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

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.main import app
from backend.api import get_db

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestUserAuth:
    def test_register_user(self):
        response = client.post(
            "/api/v1/users/register",
            json={"email": "test@example.com", "password": "SecurePassword123!"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True

    def test_register_duplicate_email(self):
        client.post(
            "/api/v1/users/register",
            json={"email": "duplicate@example.com", "password": "SecurePassword123!"},
        )
        response = client.post(
            "/api/v1/users/register",
            json={"email": "duplicate@example.com", "password": "AnotherPassword456!"},
        )
        assert response.status_code == 400

    def test_login_user(self):
        client.post(
            "/api/v1/users/register",
            json={"email": "login@example.com", "password": "SecurePassword123!"},
        )
        response = client.post(
            "/api/v1/users/login",
            data={"username": "login@example.com", "password": "SecurePassword123!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self):
        client.post(
            "/api/v1/users/register",
            json={"email": "wrong@example.com", "password": "CorrectPassword123!"},
        )
        response = client.post(
            "/api/v1/users/login",
            data={"username": "wrong@example.com", "password": "WrongPassword456!"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        response = client.post(
            "/api/v1/users/login",
            data={"username": "nonexistent@example.com", "password": "Password123!"},
        )
        assert response.status_code == 401

    def test_get_current_user(self):
        register_resp = client.post(
            "/api/v1/users/register",
            json={"email": "current@example.com", "password": "SecurePassword123!"},
        )
        user_id = register_resp.json()["id"]

        login_resp = client.post(
            "/api/v1/users/login",
            data={"username": "current@example.com", "password": "SecurePassword123!"},
        )
        token = login_resp.json()["access_token"]

        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == "current@example.com"

    def test_get_current_user_without_token(self):
        response = client.get("/api/v1/users/me")
        assert response.status_code == 403


class TestBiometricEndpoints:
    @staticmethod
    def get_auth_token():
        client.post(
            "/api/v1/users/register",
            json={"email": "biometric@example.com", "password": "SecurePassword123!"},
        )
        resp = client.post(
            "/api/v1/users/login",
            data={"username": "biometric@example.com", "password": "SecurePassword123!"},
        )
        return resp.json()["access_token"]

    def test_create_baseline(self):
        token = self.get_auth_token()
        payload = {
            "user_id": "1",
            "events": [
                {"type": "keypress", "timestamp": 100.0},
                {"type": "keypress", "timestamp": 105.0},
                {"type": "keypress", "timestamp": 110.0},
                {"type": "mousemove", "timestamp": 100.0, "x": 100.0, "y": 50.0},
                {"type": "mousemove", "timestamp": 102.0, "x": 105.0, "y": 55.0},
            ],
        }

        response = client.post(
            "/api/v1/baseline",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == "1"
        assert data["confidence"] > 0

    def test_create_baseline_user_mismatch(self):
        token = self.get_auth_token()
        payload = {
            "user_id": "999",
            "events": [
                {"type": "keypress", "timestamp": 100.0},
            ],
        }

        response = client.post(
            "/api/v1/baseline",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_analyze_behavior(self):
        token = self.get_auth_token()

        # First create baseline
        baseline_payload = {
            "user_id": "1",
            "events": [
                {"type": "keypress", "timestamp": 100.0},
                {"type": "keypress", "timestamp": 105.0},
                {"type": "keypress", "timestamp": 110.0},
            ],
        }
        client.post(
            "/api/v1/baseline",
            json=baseline_payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        # Then analyze
        analysis_payload = {
            "user_id": "1",
            "events": [
                {"type": "keypress", "timestamp": 100.0},
                {"type": "keypress", "timestamp": 105.0},
                {"type": "keypress", "timestamp": 110.0},
            ],
        }
        response = client.post(
            "/api/v1/analyze",
            json=analysis_payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "is_legitimate" in data
        assert "confidence" in data
        assert "risk_level" in data

    def test_risk_assessment(self):
        token = self.get_auth_token()
        payload = {
            "user_id": "1",
            "biometric_analysis": {"overall_score": 0.8},
            "behavioral_analysis": {"confidence": 0.85},
            "context": {
                "device": {"is_registered": True},
                "location": {},
                "attempt_history": {},
            },
        }

        response = client.post(
            "/api/v1/risk",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "risk_score" in data
        assert "risk_level" in data
        assert "additional_verification_needed" in data


class TestHealthEndpoints:
    def test_health_check(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    def test_root_health(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["app"] == "Deepshield"

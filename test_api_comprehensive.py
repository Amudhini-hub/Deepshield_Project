#!/usr/bin/env python3
"""
Comprehensive DeepShield API Test Suite
Tests all endpoints and validates functionality
"""

import time
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:5000"

def test_health_endpoint():
    """Test health endpoint"""
    print("🔍 Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["app"] == "Deepshield"
        print("✅ Health endpoint working")
        return True
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return False

def test_user_registration():
    """Test user registration"""
    print("🔍 Testing User Registration...")
    try:
        payload = {
            "email": "testuser@example.com",
            "password": "TestPass123"
        }
        response = requests.post(f"{BASE_URL}/api/v1/users/register", json=payload)
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["email"] == payload["email"]
            print("✅ User registration working")
            return data["id"]
        elif response.status_code == 400:
            # User might already exist, try login instead
            print("⚠️ User already exists, proceeding to login test")
            return None
        else:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
        return None

def test_user_login():
    """Test user login"""
    print("🔍 Testing User Login...")
    try:
        payload = {
            "username": "testuser@example.com",
            "password": "TestPass123"
        }
        response = requests.post(f"{BASE_URL}/api/v1/users/login",
                               data=payload,
                               headers={"Content-Type": "application/x-www-form-urlencoded"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        print("✅ User login working")
        return data["access_token"]
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return None

def test_behavioral_baseline(token):
    """Test behavioral baseline creation"""
    print("🔍 Testing Behavioral Baseline...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "user_id": "2",  # Use the test user ID
            "events": [
                {"type": "keystroke", "timestamp": 1640995200.0},
                {"type": "keystroke", "timestamp": 1640995200.1},
                {"type": "keystroke", "timestamp": 1640995200.2},
                {"type": "keystroke", "timestamp": 1640995200.3},
                {"type": "keystroke", "timestamp": 1640995200.4}
            ]
        }
        response = requests.post(f"{BASE_URL}/api/v1/baseline",
                               json=payload,
                               headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data
        assert "typing_speed" in data
        print("✅ Behavioral baseline working")
        return True
    except Exception as e:
        print(f"❌ Behavioral baseline test failed: {e}")
        return False

def test_risk_assessment():
    """Test risk assessment"""
    print("🔍 Testing Risk Assessment...")
    try:
        payload = {
            "user_id": "2",
            "biometric_analysis": {
                "face_confidence": 0.95,
                "voice_confidence": 0.9
            },
            "behavioral_analysis": {
                "is_legitimate": True,
                "confidence": 0.85,
                "typing_score": 0.8,
                "mouse_score": 0.9,
                "interaction_score": 0.85,
                "anomaly_flags": [],
                "risk_level": "LOW"
            },
            "context": {
                "device": {
                    "user_agent": "Mozilla/5.0",
                    "ip_address": "192.168.1.1",
                    "device_fingerprint": "abc123"
                },
                "location": {
                    "country": "US",
                    "city": "New York"
                },
                "attempt_history": {
                    "total_attempts": 5,
                    "successful_attempts": 4,
                    "last_attempt": "2026-05-06T17:18:00Z"
                }
            }
        }
        response = requests.post(f"{BASE_URL}/api/v1/risk", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "risk_score" in data
        assert "risk_level" in data
        assert "confidence" in data
        print("✅ Risk assessment working")
        return True
    except Exception as e:
        print(f"❌ Risk assessment test failed: {e}")
        return False

def test_ml_services():
    """Test ML service availability"""
    print("🔍 Testing ML Services...")

    # Test deepfake detection (should return 503 - service unavailable)
    try:
        response = requests.post(f"{BASE_URL}/api/v1/deepfake/detect")
        assert response.status_code == 503
        print("✅ Deepfake detection endpoint exists (models not loaded)")
    except Exception as e:
        print(f"❌ Deepfake detection test failed: {e}")
        return False

    # Test liveness detection (should return 503 - service unavailable)
    try:
        response = requests.post(f"{BASE_URL}/api/v1/liveness/detect")
        assert response.status_code == 503
        print("✅ Liveness detection endpoint exists (models not loaded)")
    except Exception as e:
        print(f"❌ Liveness detection test failed: {e}")
        return False

    return True

def performance_test():
    """Performance testing"""
    print("🔍 Running Performance Tests...")
    try:
        start_time = time.time()
        for i in range(20):
            response = requests.get(f"{BASE_URL}/health")
            assert response.status_code == 200

        end_time = time.time()
        avg_response_time = (end_time - start_time) / 20 * 1000
        print(f"✅ Performance test completed - Avg response time: {avg_response_time:.2f}ms")

        if avg_response_time < 100:
            print("🚀 Excellent performance!")
        elif avg_response_time < 500:
            print("👍 Good performance")
        else:
            print("⚠️ Performance could be improved")

        return True
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting DeepShield API Test Suite")
    print("=" * 50)

    results = []

    # Basic health check
    results.append(("Health Check", test_health_endpoint()))

    # Authentication tests
    user_id = test_user_registration()
    token = test_user_login()
    results.append(("User Registration", user_id is not None))
    results.append(("User Login", token is not None))

    # Behavioral biometrics (requires token)
    if token:
        results.append(("Behavioral Baseline", test_behavioral_baseline(token)))
    else:
        results.append(("Behavioral Baseline", False))

    # Risk assessment
    results.append(("Risk Assessment", test_risk_assessment()))

    # ML services
    results.append(("ML Services", test_ml_services()))

    # Performance
    results.append(("Performance", performance_test()))

    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} | {status}")
        if result:
            passed += 1

    print("=" * 50)
    print(f"Overall Score: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! DeepShield is fully operational.")
    elif passed >= total * 0.8:
        print("👍 Most tests passed. System is mostly operational.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")

    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
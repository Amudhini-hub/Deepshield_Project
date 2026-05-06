"""
Quick API Validation Script - Tier 1 Implementation
Tests all critical endpoints to verify functionality
"""

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, drop_db

def test_api():
    """Test all critical API endpoints"""
    
    # Initialize database
    init_db()
    client = TestClient(app)
    
    tests_passed = 0
    tests_failed = 0
    
    try:
        # Test 1: Health Check
        print("\n" + "="*70)
        print("TEST 1: Health Check Endpoint")
        print("="*70)
        response = client.get("/api/v1/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "ok", "Health status not OK"
        print("✅ PASSED")
        tests_passed += 1
        
        # Test 2: Register User
        print("\n" + "="*70)
        print("TEST 2: Register New User")
        print("="*70)
        register_data = {
            "email": "testuser@example.com",
            "password": "SecurePass123"
        }
        response = client.post("/api/v1/users/register", json=register_data)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        user = response.json()
        assert user["email"] == register_data["email"], "Email mismatch"
        assert user["is_active"] is True, "User should be active"
        user_id = user["id"]
        print(f"✅ PASSED - User created with ID: {user_id}")
        tests_passed += 1
        
        # Test 3: Duplicate Registration
        print("\n" + "="*70)
        print("TEST 3: Prevent Duplicate Email Registration")
        print("="*70)
        response = client.post("/api/v1/users/register", json=register_data)
        assert response.status_code == 400, f"Expected 400 for duplicate, got {response.status_code}"
        print("✅ PASSED - Duplicate registration prevented")
        tests_passed += 1
        
        # Test 4: Login User
        print("\n" + "="*70)
        print("TEST 4: Login and Get Tokens")
        print("="*70)
        response = client.post(
            "/api/v1/users/login",
            data={"username": register_data["email"], "password": register_data["password"]}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        tokens = response.json()
        assert "access_token" in tokens, "No access token"
        assert "refresh_token" in tokens, "No refresh token"
        assert tokens["token_type"] == "bearer", "Wrong token type"
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        print(f"✅ PASSED - Access token obtained")
        print(f"   Access Token: {access_token[:30]}...")
        print(f"   Expires in: {tokens['expires_in']} seconds")
        tests_passed += 1
        
        # Test 5: Get User Profile
        print("\n" + "="*70)
        print("TEST 5: Get Authenticated User Profile")
        print("="*70)
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        profile = response.json()
        assert profile["email"] == register_data["email"], "Email mismatch in profile"
        assert profile["id"] == user_id, "User ID mismatch"
        print(f"✅ PASSED - Profile retrieved for {profile['email']}")
        tests_passed += 1
        
        # Test 6: Refresh Token
        print("\n" + "="*70)
        print("TEST 6: Refresh Access Token")
        print("="*70)
        response = client.post(
            "/api/v1/users/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        new_tokens = response.json()
        assert "access_token" in new_tokens, "No access token in refresh response"
        assert new_tokens["access_token"] != access_token, "Access token should be refreshed"
        print(f"✅ PASSED - New access token obtained")
        tests_passed += 1
        
        # Test 7: Invalid Login
        print("\n" + "="*70)
        print("TEST 7: Invalid Login Credentials")
        print("="*70)
        response = client.post(
            "/api/v1/users/login",
            data={"username": register_data["email"], "password": "WrongPassword123"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ PASSED - Wrong password rejected")
        tests_passed += 1
        
        # Test 8: Update User Profile
        print("\n" + "="*70)
        print("TEST 8: Update User Profile")
        print("="*70)
        response = client.put(
            "/api/v1/users/profile",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"email": "newemail@example.com"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        updated = response.json()
        assert updated["email"] == "newemail@example.com", "Email not updated"
        print(f"✅ PASSED - Email updated to {updated['email']}")
        tests_passed += 1
        
        # Test 9: Logout
        print("\n" + "="*70)
        print("TEST 9: Logout User")
        print("="*70)
        response = client.post(
            "/api/v1/users/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        logout_result = response.json()
        assert logout_result["status"] == "success", "Logout failed"
        print("✅ PASSED - User logged out successfully")
        tests_passed += 1
        
        # Test 10: Invalid Token
        print("\n" + "="*70)
        print("TEST 10: Reject Invalid Token")
        print("="*70)
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid_token_xyz"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ PASSED - Invalid token rejected")
        tests_passed += 1
        
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
        tests_failed += 1
    except Exception as e:
        print(f"❌ ERROR: {e}")
        tests_failed += 1
    finally:
        drop_db()
    
    # Summary
    print("\n" + "="*70)
    print(f"TEST SUMMARY: {tests_passed} passed, {tests_failed} failed")
    print("="*70)
    
    if tests_failed == 0:
        print("\n🎉 ALL TESTS PASSED! API TIER 1 IMPLEMENTATION COMPLETE!")
        return True
    else:
        print(f"\n⚠️  {tests_failed} TEST(S) FAILED")
        return False

if __name__ == "__main__":
    success = test_api()
    exit(0 if success else 1)

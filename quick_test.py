"""Quick validation to file"""
import sys
sys.stdout = open('test_output.log', 'w')
sys.stderr = open('test_error.log', 'w')

try:
    print("="*70)
    print("DeepShield Tier 1 API - Validation Test")
    print("="*70)
    
    from backend.database import init_db, drop_db
    from fastapi.testclient import TestClient
    from backend.main import app
    
    init_db()
    client = TestClient(app)
    
    print("\n[1/5] Testing Health Endpoint...")
    resp = client.get("/api/v1/health")
    print(f"    Status: {resp.status_code}")
    assert resp.status_code == 200
    print("    ✓ PASSED")
    
    print("\n[2/5] Testing User Registration...")
    resp = client.post("/api/v1/users/register", json={
        "email": "test@example.com",
        "password": "TestPass123"
    })
    print(f"    Status: {resp.status_code}")
    assert resp.status_code == 201
    print("    ✓ PASSED")
    
    print("\n[3/5] Testing Login...")
    resp = client.post("/api/v1/users/login", data={
        "username": "test@example.com",
        "password": "TestPass123"
    })
    print(f"    Status: {resp.status_code}")
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    print("    ✓ PASSED")
    
    print("\n[4/5] Testing Get Profile...")
    resp = client.get("/api/v1/users/me", headers={
        "Authorization": f"Bearer {token}"
    })
    print(f"    Status: {resp.status_code}")
    assert resp.status_code == 200
    print("    ✓ PASSED")
    
    print("\n[5/5] Testing Logout...")
    resp = client.post("/api/v1/users/logout", headers={
        "Authorization": f"Bearer {token}"
    })
    print(f"    Status: {resp.status_code}")
    assert resp.status_code == 200
    print("    ✓ PASSED")
    
    drop_db()
    
    print("\n" + "="*70)
    print("✅ ALL TIER 1 TESTS PASSED!")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

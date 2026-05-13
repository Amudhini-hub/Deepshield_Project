#!/usr/bin/env python3
"""
Quick validation script for Redis Integration
Tests all key components without requiring full test framework
"""

import sys
import time
from datetime import datetime

def test_redis_connection():
    """Test 1: Redis Connection"""
    print("\n" + "="*60)
    print("TEST 1: Redis Connection")
    print("="*60)
    try:
        from backend.redis_manager import get_redis_manager
        redis_mgr = get_redis_manager()
        
        if redis_mgr.is_connected():
            print("✅ Redis connected successfully")
            stats = redis_mgr.get_redis_stats()
            print(f"   - Status: {stats['status']}")
            print(f"   - Memory used: {stats.get('used_memory_mb', 'N/A')} MB")
            print(f"   - Connected clients: {stats.get('connected_clients', 'N/A')}")
            return True
        else:
            print("❌ Redis not connected")
            return False
    except Exception as e:
        print(f"❌ Error testing Redis connection: {e}")
        return False


def test_session_management():
    """Test 2: Session Management"""
    print("\n" + "="*60)
    print("TEST 2: Session Management")
    print("="*60)
    try:
        from backend.redis_manager import get_redis_manager
        redis_mgr = get_redis_manager()
        
        # Create session
        session_data = {"device": "test_device", "ip": "127.0.0.1"}
        session_id = redis_mgr.create_session("test_user", session_data)
        print(f"✅ Session created: {session_id}")
        
        # Retrieve session
        retrieved = redis_mgr.get_session(session_id)
        if retrieved and retrieved["user_id"] == "test_user":
            print(f"✅ Session retrieved successfully")
            print(f"   - User ID: {retrieved['user_id']}")
            print(f"   - Data: {retrieved['data']}")
        else:
            print("❌ Failed to retrieve session")
            return False
        
        # Check session count
        count = redis_mgr.get_session_count("test_user")
        print(f"✅ Active sessions for user: {count}")
        
        # Delete session
        redis_mgr.delete_session(session_id, "test_user")
        if redis_mgr.get_session(session_id) is None:
            print("✅ Session deleted successfully")
        else:
            print("❌ Failed to delete session")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error testing session management: {e}")
        return False


def test_rate_limiting():
    """Test 3: Rate Limiting"""
    print("\n" + "="*60)
    print("TEST 3: Rate Limiting")
    print("="*60)
    try:
        from backend.redis_manager import get_redis_manager
        redis_mgr = get_redis_manager()
        
        key = "rate_limit:test:api"
        limit = 3
        window = 60
        
        # Test rate limit
        allowed_count = 0
        for i in range(5):
            if redis_mgr.check_rate_limit(key, limit=limit, window_seconds=window):
                allowed_count += 1
                print(f"   Request {i+1}: ✅ Allowed")
            else:
                print(f"   Request {i+1}: ❌ Rate limit exceeded")
        
        if allowed_count == limit:
            print(f"✅ Rate limiting working correctly (allowed {allowed_count}/{limit})")
        else:
            print(f"❌ Rate limiting not working as expected")
            return False
        
        # Check status
        status = redis_mgr.get_rate_limit_status(key, limit=limit, window_seconds=window)
        print(f"✅ Rate limit status:")
        print(f"   - Limit: {status['limit']}")
        print(f"   - Current: {status['current']}")
        print(f"   - Remaining: {status['remaining']}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing rate limiting: {e}")
        return False


def test_token_blacklisting():
    """Test 4: Token Blacklisting"""
    print("\n" + "="*60)
    print("TEST 4: Token Blacklisting")
    print("="*60)
    try:
        from backend.redis_manager import get_redis_manager
        redis_mgr = get_redis_manager()
        
        test_token = "test_token_12345"
        
        # Initially not blacklisted
        if not redis_mgr.is_token_blacklisted(test_token):
            print("✅ Token not blacklisted initially")
        else:
            print("❌ Token should not be blacklisted initially")
            return False
        
        # Blacklist token
        redis_mgr.blacklist_token(test_token, expires_in_seconds=3600)
        print("✅ Token blacklisted")
        
        # Verify blacklist
        if redis_mgr.is_token_blacklisted(test_token):
            print("✅ Token confirmed as blacklisted")
        else:
            print("❌ Token blacklist verification failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error testing token blacklisting: {e}")
        return False


def test_caching():
    """Test 5: Caching Operations"""
    print("\n" + "="*60)
    print("TEST 5: Caching Operations")
    print("="*60)
    try:
        from backend.redis_manager import get_redis_manager
        redis_mgr = get_redis_manager()
        
        key = "cache:test:profile"
        value = {"name": "Test User", "email": "test@example.com"}
        
        # Set cache
        redis_mgr.set_cache(key, value, expires_in_seconds=3600)
        print("✅ Cache value set")
        
        # Get cache
        cached = redis_mgr.get_cache(key)
        if cached == value:
            print("✅ Cache value retrieved correctly")
            print(f"   - Cached: {cached}")
        else:
            print("❌ Cache value mismatch")
            return False
        
        # Delete cache
        redis_mgr.delete_cache(key)
        if redis_mgr.get_cache(key) is None:
            print("✅ Cache value deleted")
        else:
            print("❌ Failed to delete cache value")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error testing caching: {e}")
        return False


def test_configuration():
    """Test 6: Configuration"""
    print("\n" + "="*60)
    print("TEST 6: Configuration")
    print("="*60)
    try:
        from backend.config.config import get_config
        config = get_config()
        
        # Check Redis configuration
        print(f"✅ Configuration loaded:")
        print(f"   - REDIS_HOST: {getattr(config, 'REDIS_HOST', 'localhost')}")
        print(f"   - REDIS_PORT: {getattr(config, 'REDIS_PORT', 6379)}")
        print(f"   - REDIS_DB: {getattr(config, 'REDIS_DB', 0)}")
        print(f"   - REDIS_ENABLED: {getattr(config, 'REDIS_ENABLED', True)}")
        print(f"   - JWT_EXPIRATION_HOURS: {config.JWT_EXPIRATION_HOURS}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("DeepShield Redis Integration - Validation Tests")
    print("="*60)
    print(f"Started at: {datetime.now().isoformat()}")
    
    results = []
    
    # Run tests
    results.append(("Redis Connection", test_redis_connection()))
    results.append(("Session Management", test_session_management()))
    results.append(("Rate Limiting", test_rate_limiting()))
    results.append(("Token Blacklisting", test_token_blacklisting()))
    results.append(("Caching", test_caching()))
    results.append(("Configuration", test_configuration()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Completed at: {datetime.now().isoformat()}")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

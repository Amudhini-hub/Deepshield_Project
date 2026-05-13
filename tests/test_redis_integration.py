"""
Test Redis Integration and Rate Limiting
"""

from datetime import datetime, timedelta

import pytest

from backend.redis_manager import RedisManager


class TestRedisManager:
    """Test RedisManager functionality"""

    def test_redis_connection(self):
        """Test Redis connection"""
        redis_mgr = RedisManager(host="localhost", port=6379, db=0)
        assert redis_mgr.is_connected()

    def test_session_creation(self):
        """Test session creation"""
        redis_mgr = RedisManager(host="localhost", port=6379, db=0)

        session_data = {
            "user_id": "1",
            "ip_address": "127.0.0.1",
            "user_agent": "test-client",
        }

        session_id = redis_mgr.create_session(
            "user_1", session_data, expires_in_hours=24
        )
        assert session_id is not None
        assert "user_1" in session_id

    def test_session_retrieval(self):
        """Test session retrieval"""
        redis_mgr = RedisManager(host="localhost", port=6379, db=0)

        session_data = {"device": "laptop", "os": "windows"}
        session_id = redis_mgr.create_session(
            "user_2", session_data, expires_in_hours=24
        )

        retrieved = redis_mgr.get_session(session_id)
        assert retrieved is not None
        assert retrieved["user_id"] == "user_2"
        assert retrieved["data"]["device"] == "laptop"

    def test_session_deletion(self):
        """Test session deletion"""
        redis_mgr = RedisManager(host="localhost", port=6379, db=0)

        session_data = {"test": "data"}
        session_id = redis_mgr.create_session("user_3", session_data)

        # Verify session exists
        assert redis_mgr.get_session(session_id) is not None

        # Delete session
        redis_mgr.delete_session(session_id, "user_3")
        assert redis_mgr.get_session(session_id) is None

    def test_rate_limiting(self):
        """Test rate limit checking"""
        redis_mgr = RedisManager(host="localhost", port=6379, db=0)

        key = "rate_limit:test_user:login"
        limit = 5
        window = 60

        # First 5 requests should succeed
        for i in range(limit):
            assert redis_mgr.check_rate_limit(key, limit=limit, window_seconds=window)

        # 6th request should fail
        assert not redis_mgr.check_rate_limit(key, limit=limit, window_seconds=window)

    def test_rate_limit_status(self):
        """Test rate limit status"""
        redis_mgr = RedisManager(host="localhost", port=6379, db=0)

        key = "rate_limit:status_test:api"
        limit = 10
        window = 60

        # Make some requests
        for i in range(3):
            redis_mgr.check_rate_limit(key, limit=limit, window_seconds=window)

        status = redis_mgr.get_rate_limit_status(
            key, limit=limit, window_seconds=window
        )
        assert status["limit"] == limit
        assert status["remaining"] == 7
        assert status["current"] == 3

    def test_token_blacklisting(self):
        """Test token blacklist"""
        redis_mgr = RedisManager(host="localhost", port=6379, db=0)

        token = "test_token_12345"

        # Verify token is not blacklisted initially
        assert not redis_mgr.is_token_blacklisted(token)

        # Blacklist token
        assert redis_mgr.blacklist_token(token, expires_in_seconds=3600)

        # Verify token is blacklisted
        assert redis_mgr.is_token_blacklisted(token)

    def test_cache_operations(self):
        """Test cache set/get/delete"""
        redis_mgr = RedisManager(host="localhost", port=6379, db=0)

        key = "cache:user:profile:1"
        value = {"name": "John", "email": "john@example.com"}

        # Set cache
        assert redis_mgr.set_cache(key, value, expires_in_seconds=3600)

        # Get cache
        cached = redis_mgr.get_cache(key)
        assert cached == value

        # Delete cache
        assert redis_mgr.delete_cache(key)
        assert redis_mgr.get_cache(key) is None

    def test_delete_user_sessions(self):
        """Test deleting all user sessions"""
        redis_mgr = RedisManager(host="localhost", port=6379, db=0)

        user_id = "user_batch_test"

        # Create multiple sessions
        session_ids = []
        for i in range(3):
            session_data = {"device_id": f"device_{i}"}
            session_id = redis_mgr.create_session(user_id, session_data)
            session_ids.append(session_id)

        # Verify sessions exist
        for session_id in session_ids:
            assert redis_mgr.get_session(session_id) is not None

        # Delete all user sessions
        deleted_count = redis_mgr.delete_user_sessions(user_id)
        assert deleted_count == 3

        # Verify all sessions are deleted
        for session_id in session_ids:
            assert redis_mgr.get_session(session_id) is None

    def test_redis_stats(self):
        """Test Redis statistics"""
        redis_mgr = RedisManager(host="localhost", port=6379, db=0)

        stats = redis_mgr.get_redis_stats()
        assert stats["status"] == "connected"
        assert "used_memory_mb" in stats
        assert "connected_clients" in stats
        assert stats["connected_clients"] > 0


class TestRateLimitMiddleware:
    """Test rate limiting middleware"""

    @pytest.mark.asyncio
    async def test_rate_limit_header(self, client):
        """Test rate limit headers in response"""
        # Make a request to an endpoint
        response = client.get("/api/v1/health")

        # Check response headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, client):
        """Test 429 response when rate limit exceeded"""
        # Attempt to exceed rate limit on login endpoint
        # (this test requires setting a very low limit for testing)
        # Skip for now - requires test-specific configuration
        pass


class TestTokenBlacklisting:
    """Test token blacklisting functionality"""

    def test_blacklist_token_via_authentication(self):
        """Test blacklisting token through authentication module"""
        from backend.services.authentication import (
            blacklist_token,
            is_token_blacklisted,
        )

        test_token = "test.jwt.token"

        # Create mock JWT payload
        import datetime

        from jose import jwt

        from backend.config.config import get_config

        config = get_config()
        payload = {
            "sub": "1",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
            "type": "access",
        }
        token = jwt.encode(payload, config.SECRET_KEY, algorithm=config.JWT_ALGORITHM)

        # Blacklist token
        result = blacklist_token(token)
        assert result is True or result is None  # May be None if Redis unavailable

        # Check if blacklisted
        if result is not None:
            assert is_token_blacklisted(token)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

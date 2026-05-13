"""
Redis Manager for DeepShield
Handles caching, session management, and rate limiting
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RedisManager:
    """Centralized Redis connection and operations manager"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str = None,
    ):
        """
        Initialize Redis connection pool

        Args:
            host: Redis server host
            port: Redis server port
            db: Database number
            password: Optional password
        """
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30,
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Redis connected: {host}:{port}")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except RedisError:
            return False

    # ============ SESSION MANAGEMENT ============

    def create_session(
        self, user_id: str, session_data: Dict[str, Any], expires_in_hours: int = 24
    ) -> str:
        """
        Create a new session for a user

        Args:
            user_id: User ID
            session_data: Session data to store
            expires_in_hours: Session expiration time in hours

        Returns:
            Session ID
        """
        if not self.redis_client:
            logger.warning("Redis not available, session not stored")
            return None

        try:
            session_id = f"session:{user_id}:{datetime.utcnow().timestamp()}"
            session_payload = {
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "data": session_data,
            }

            ttl_seconds = expires_in_hours * 3600
            self.redis_client.setex(
                session_id, ttl_seconds, json.dumps(session_payload)
            )

            # Add to user sessions set for tracking
            self.redis_client.sadd(f"user_sessions:{user_id}", session_id)
            logger.info(f"Session created for user {user_id}: {session_id}")
            return session_id
        except RedisError as e:
            logger.error(f"Error creating session: {e}")
            return None

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve session data

        Args:
            session_id: Session ID

        Returns:
            Session data or None
        """
        if not self.redis_client:
            return None

        try:
            session_data = self.redis_client.get(session_id)
            if session_data:
                return json.loads(session_data)
            return None
        except RedisError as e:
            logger.error(f"Error retrieving session: {e}")
            return None

    def delete_session(self, session_id: str, user_id: str = None) -> bool:
        """
        Delete a session

        Args:
            session_id: Session ID
            user_id: Optional user ID for cleanup

        Returns:
            Success status
        """
        if not self.redis_client:
            return False

        try:
            self.redis_client.delete(session_id)
            if user_id:
                self.redis_client.srem(f"user_sessions:{user_id}", session_id)
            logger.info(f"Session deleted: {session_id}")
            return True
        except RedisError as e:
            logger.error(f"Error deleting session: {e}")
            return False

    def delete_user_sessions(self, user_id: str) -> int:
        """
        Delete all sessions for a user (logout all devices)

        Args:
            user_id: User ID

        Returns:
            Number of sessions deleted
        """
        if not self.redis_client:
            return 0

        try:
            session_ids = self.redis_client.smembers(f"user_sessions:{user_id}")
            if session_ids:
                self.redis_client.delete(*session_ids)
                self.redis_client.delete(f"user_sessions:{user_id}")
                logger.info(f"Deleted {len(session_ids)} sessions for user {user_id}")
                return len(session_ids)
            return 0
        except RedisError as e:
            logger.error(f"Error deleting user sessions: {e}")
            return 0

    # ============ RATE LIMITING ============

    def check_rate_limit(
        self, key: str, limit: int = 100, window_seconds: int = 60
    ) -> bool:
        """
        Check if a request exceeds rate limit

        Args:
            key: Rate limit key (e.g., "rate_limit:user_id:endpoint")
            limit: Max requests allowed
            window_seconds: Time window in seconds

        Returns:
            True if request is allowed, False if limit exceeded
        """
        if not self.redis_client:
            return True  # Allow if Redis unavailable

        try:
            current = self.redis_client.incr(key)
            if current == 1:
                self.redis_client.expire(key, window_seconds)
            return current <= limit
        except RedisError as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow on error

    def get_rate_limit_status(
        self, key: str, limit: int = 100, window_seconds: int = 60
    ) -> Dict[str, Any]:
        """
        Get rate limit status for a key

        Args:
            key: Rate limit key
            limit: Max requests allowed
            window_seconds: Time window in seconds

        Returns:
            Dictionary with remaining, limit, and reset_at
        """
        if not self.redis_client:
            return {"remaining": limit, "limit": limit, "reset_at": None}

        try:
            current = self.redis_client.get(key)
            current = int(current) if current else 0
            ttl = self.redis_client.ttl(key)

            remaining = max(0, limit - current)
            reset_at = None
            if ttl > 0:
                reset_at = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()

            return {
                "remaining": remaining,
                "limit": limit,
                "reset_at": reset_at,
                "current": current,
            }
        except RedisError as e:
            logger.error(f"Error getting rate limit status: {e}")
            return {"remaining": limit, "limit": limit, "reset_at": None}

    # ============ TOKEN BLACKLIST ============

    def blacklist_token(self, token: str, expires_in_seconds: int = 3600) -> bool:
        """
        Add token to blacklist (for logout)

        Args:
            token: Token to blacklist
            expires_in_seconds: TTL in seconds

        Returns:
            Success status
        """
        if not self.redis_client:
            return False

        try:
            key = f"blacklist:{token}"
            self.redis_client.setex(key, expires_in_seconds, "1")
            logger.info(f"Token blacklisted: {token[:20]}...")
            return True
        except RedisError as e:
            logger.error(f"Error blacklisting token: {e}")
            return False

    def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if token is blacklisted

        Args:
            token: Token to check

        Returns:
            True if blacklisted, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            key = f"blacklist:{token}"
            return self.redis_client.exists(key) > 0
        except RedisError as e:
            logger.error(f"Error checking token blacklist: {e}")
            return False

    # ============ CACHING ============

    def set_cache(self, key: str, value: Any, expires_in_seconds: int = 3600) -> bool:
        """
        Set a cache value

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            expires_in_seconds: TTL in seconds

        Returns:
            Success status
        """
        if not self.redis_client:
            return False

        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            self.redis_client.setex(key, expires_in_seconds, str(value))
            return True
        except RedisError as e:
            logger.error(f"Error setting cache: {e}")
            return False

    def get_cache(self, key: str) -> Optional[Any]:
        """
        Get a cache value

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.redis_client:
            return None

        try:
            value = self.redis_client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except RedisError as e:
            logger.error(f"Error getting cache: {e}")
            return None

    def delete_cache(self, key: str) -> bool:
        """
        Delete a cache value

        Args:
            key: Cache key

        Returns:
            Success status
        """
        if not self.redis_client:
            return False

        try:
            self.redis_client.delete(key)
            return True
        except RedisError as e:
            logger.error(f"Error deleting cache: {e}")
            return False

    def clear_cache_pattern(self, pattern: str) -> int:
        """
        Clear all cache keys matching a pattern

        Args:
            pattern: Redis pattern (e.g., "cache:user:*")

        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries matching {pattern}")
                return len(keys)
            return 0
        except RedisError as e:
            logger.error(f"Error clearing cache pattern: {e}")
            return 0

    # ============ MONITORING & STATS ============

    def get_redis_stats(self) -> Dict[str, Any]:
        """
        Get Redis server statistics

        Returns:
            Dictionary with Redis stats
        """
        if not self.redis_client:
            return {"status": "disconnected"}

        try:
            info = self.redis_client.info()
            return {
                "status": "connected",
                "used_memory_mb": info.get("used_memory", 0) / 1024 / 1024,
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            }
        except RedisError as e:
            logger.error(f"Error getting Redis stats: {e}")
            return {"status": "error", "error": str(e)}

    def get_session_count(self, user_id: str = None) -> int:
        """
        Get number of active sessions

        Args:
            user_id: Optional user ID for specific user's sessions

        Returns:
            Number of sessions
        """
        if not self.redis_client:
            return 0

        try:
            if user_id:
                return self.redis_client.scard(f"user_sessions:{user_id}")
            else:
                # Count all session keys
                return len(self.redis_client.keys("session:*"))
        except RedisError as e:
            logger.error(f"Error getting session count: {e}")
            return 0


# Singleton instance
_redis_manager = None


def get_redis_manager(
    host: str = "localhost", port: int = 6379, db: int = 0, password: str = None
) -> RedisManager:
    """Get or create Redis manager singleton"""
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = RedisManager(host=host, port=port, db=db, password=password)
    return _redis_manager

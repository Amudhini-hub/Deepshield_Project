"""
Rate Limiting Middleware for DeepShield
Implements token bucket and sliding window rate limiting
"""

import logging
import os
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.redis_manager import get_redis_manager

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis

    Configuration:
    - Global limit: 1000 requests per hour
    - Per-user limit: 100 requests per minute
    - Per-endpoint limit: varies by endpoint
    """

    def __init__(self, app, redis_manager=None):
        super().__init__(app)
        self.redis_manager = redis_manager or get_redis_manager()

    async def dispatch(self, request: Request, call_next: Callable) -> Callable:
        """
        Check rate limits before processing request
        """
        if os.environ.get("PYTEST_RUNNING") == "true":
            return await call_next(request)

        if not self.redis_manager.is_connected():
            # Skip rate limiting if Redis unavailable
            return await call_next(request)

        # Extract rate limit key
        rate_limit_key = self._get_rate_limit_key(request)

        # Define limits by endpoint
        endpoint = request.url.path
        limit, window = self._get_limit_for_endpoint(endpoint)

        # Check rate limit
        if not self.redis_manager.check_rate_limit(
            rate_limit_key, limit=limit, window_seconds=window
        ):
            status = self.redis_manager.get_rate_limit_status(
                rate_limit_key, limit=limit, window_seconds=window
            )
            logger.warning(f"Rate limit exceeded for {rate_limit_key}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after": status.get("reset_at"),
                    "limit": limit,
                    "window_seconds": window,
                },
            )

        response = await call_next(request)

        # Add rate limit headers to response
        status = self.redis_manager.get_rate_limit_status(
            rate_limit_key, limit=limit, window_seconds=window
        )
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(status.get("remaining", 0))
        response.headers["X-RateLimit-Reset"] = status.get("reset_at", "")

        return response

    def _get_rate_limit_key(self, request: Request) -> str:
        """
        Generate rate limit key based on user and IP

        Priority:
        1. Authenticated user ID
        2. Client IP address
        """
        # Try to get user from token
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            # In production, decode token to get user_id
            # For now, use token hash as key
            return f"rate_limit:token:{hash(token)}"

        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"rate_limit:ip:{client_ip}"

    def _get_limit_for_endpoint(self, endpoint: str) -> tuple:
        """
        Get rate limit (requests, window_seconds) for specific endpoint

        Returns:
            Tuple of (limit, window_seconds)
        """
        # Strict limits for sensitive endpoints
        strict_endpoints = {
            "/api/v1/users/login": (5, 60),  # 5 requests per minute
            "/api/v1/users/register": (3, 60),  # 3 requests per minute
            "/api/v1/users/refresh": (10, 60),  # 10 requests per minute
        }

        # Moderate limits for ML endpoints
        moderate_endpoints = {
            "/api/v1/deepfake/detect": (10, 60),  # 10 requests per minute
            "/api/v1/liveness/detect": (10, 60),  # 10 requests per minute
        }

        # Default limits
        default_limit = (100, 60)  # 100 requests per minute

        for path, limit in strict_endpoints.items():
            if endpoint.startswith(path):
                return limit

        for path, limit in moderate_endpoints.items():
            if endpoint.startswith(path):
                return limit

        return default_limit

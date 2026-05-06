"""Structured logging middleware for FastAPI with monitoring"""

import json
import logging
import time
import uuid
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .monitoring import record_api_call, record_security_event

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging with metrics collection"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.time()

        # Skip detailed logging for health checks and metrics endpoints
        is_health_check = request.url.path in ["/health", "/", "/metrics", "/metrics/health", "/metrics/api", "/metrics/security"]

        # Extract user info if available
        user_id = None
        if hasattr(request.state, 'user') and request.state.user:
            user_id = str(request.state.user.get('id', 'unknown'))

        # Extract client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        if not is_health_check:
            # Log request
            logger.info("Request started", extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": client_ip,
                "user_agent": user_agent,
                "user_id": user_id,
            })

        try:
            response = await call_next(request)
            status_code = response.status_code
            error_type = None
        except Exception as exc:
            status_code = 500
            error_type = type(exc).__name__

            if not is_health_check:
                logger.error("Request failed with exception", extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(exc),
                    "error_type": error_type,
                }, exc_info=True)
            raise

        process_time = time.time() - start_time
        response_time_ms = round(process_time * 1000, 2)

        if not is_health_check:
            # Log response
            logger.info("Request completed", extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": response_time_ms,
                "user_id": user_id,
            })

        # Record API metrics
        record_api_call(
            endpoint=request.url.path,
            method=request.method,
            response_time_ms=response_time_ms,
            status_code=status_code,
            user_id=user_id,
            error_type=error_type
        )

        # Record security events for sensitive endpoints
        if request.url.path in ["/auth/login", "/auth/register", "/api/risk-assessment"] and status_code >= 400:
            record_security_event(
                event_type="failed_authentication" if "/auth/" in request.url.path else "risk_assessment_error",
                user_id=user_id,
                ip_address=client_ip,
                user_agent=user_agent,
                action_taken="blocked" if status_code == 403 else "logged"
            )

        # Add headers to response
        response.headers["x-request-id"] = request_id
        response.headers["x-process-time"] = f"{process_time:.6f}"

        return response

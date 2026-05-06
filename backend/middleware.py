"""Structured logging middleware for FastAPI"""

import json
import logging
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        
        # Skip detailed logging for health checks
        is_health_check = request.url.path in ["/health", "/"]
        
        if not is_health_check:
            # Log request
            logger.info(f"Request started", extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client": request.client.host if request.client else "unknown",
            })
        
        try:
            response = await call_next(request)
        except Exception as exc:
            if not is_health_check:
                logger.error(f"Request failed with exception", extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(exc),
                }, exc_info=True)
            raise
        
        process_time = time.time() - start_time
        
        if not is_health_check:
            # Log response
            logger.info(f"Request completed", extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(process_time * 1000, 2),
            })
        
        # Add request ID to response headers
        response.headers["x-request-id"] = request_id
        response.headers["x-process-time"] = f"{process_time:.6f}"
        
        return response
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(process_time * 1000, 2),
        })
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

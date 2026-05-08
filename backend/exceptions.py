"""Custom exception handlers for DeepShield API"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class DeepshieldException(Exception):
    """Base exception for DeepShield"""

    def __init__(
        self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthenticationException(DeepshieldException):
    """Authentication failed"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationException(DeepshieldException):
    """User not authorized for this action"""

    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class ResourceNotFoundException(DeepshieldException):
    """Resource not found"""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ValidationException(DeepshieldException):
    """Validation error"""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class DatabaseException(DeepshieldException):
    """Database operation failed"""

    def __init__(self, message: str = "Database error"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


def register_exception_handlers(app: FastAPI):
    """Register all exception handlers with FastAPI app"""

    @app.exception_handler(DeepshieldException)
    async def deepshield_exception_handler(request: Request, exc: DeepshieldException):
        logger.error(
            f"DeepshieldException: {exc.message}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "error_type": exc.__class__.__name__},
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        logger.warning(
            f"ValidationError: {exc}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Validation error", "errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception(
            f"Unhandled exception: {exc}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

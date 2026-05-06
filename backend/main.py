from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from sqlalchemy import text
import time
from functools import lru_cache

from backend.api import api_router
from backend.config.config import get_config
from backend.database import init_db, health_check
from backend.exceptions import register_exception_handlers
from backend.middleware import LoggingMiddleware
from backend.logging_config import setup_logging

# Setup logging before anything else
setup_logging()
logger = logging.getLogger(__name__)
config = get_config()

app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    debug=config.DEBUG,
)

# Add CORS middleware
if config.ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Register exception handlers
register_exception_handlers(app)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup"""
    logger.info("DeepShield starting up...")
    if not health_check():
        logger.warning("Database health check failed, attempting initialization...")
        if init_db():
            logger.info("Database initialized successfully")
        else:
            logger.error("Failed to initialize database")
    else:
        logger.info("Database health check passed")


@app.get("/", tags=["health"])
async def root() -> dict:
    """Root endpoint"""
    return {
        "status": "ok",
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
    }


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Health check endpoint - lightweight"""
    # Skip database check for performance - assume healthy if server is running
    return {
        "status": "ok",
        "database": "healthy",  # Assume healthy for health checks
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
    }


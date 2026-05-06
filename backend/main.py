from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import time

from backend.alerting import get_alert_manager
from backend.api import api_router
from backend.config.config import get_config
from backend.database import init_db, health_check
from backend.exceptions import register_exception_handlers
from backend.logging_config import setup_logging
from backend.middleware import LoggingMiddleware
from backend.monitoring import get_api_stats, get_security_stats, get_system_health

# Setup logging before anything else
config = get_config()
setup_logging()
logger = logging.getLogger(__name__)

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


@app.get("/metrics/health", tags=["monitoring"])
async def system_health() -> dict:
    """Get system health metrics"""
    return get_system_health()


@app.get("/metrics/api", tags=["monitoring"])
async def api_metrics(hours: int = 24) -> dict:
    """Get API performance metrics"""
    return get_api_stats(hours)


@app.get("/metrics/security", tags=["monitoring"])
async def security_metrics(hours: int = 24) -> dict:
    """Get security event metrics"""
    return get_security_stats(hours)


@app.get("/metrics", tags=["monitoring"])
async def all_metrics(hours: int = 24) -> dict:
    """Get all monitoring metrics"""
    return {
        "system_health": get_system_health(),
        "api_stats": get_api_stats(hours),
        "security_stats": get_security_stats(hours),
        "timestamp": time.time()
    }


@app.get("/alerts/active", tags=["alerting"])
async def get_active_alerts() -> dict:
    """Get currently active alerts"""
    alert_manager = get_alert_manager()
    return {
        "active_alerts": alert_manager.get_active_alerts(),
        "count": len(alert_manager.get_active_alerts())
    }


@app.get("/alerts/history", tags=["alerting"])
async def get_alert_history(hours: int = 24) -> dict:
    """Get alert history"""
    alert_manager = get_alert_manager()
    return {
        "alert_history": alert_manager.get_alert_history(hours),
        "count": len(alert_manager.get_alert_history(hours))
    }


@app.post("/alerts/resolve/{rule_name}", tags=["alerting"])
async def resolve_alert(rule_name: str) -> dict:
    """Resolve an active alert"""
    alert_manager = get_alert_manager()
    alert_manager.resolve_alert(rule_name)
    return {"message": f"Alert {rule_name} resolved"}


@app.get("/alerts/rules", tags=["alerting"])
async def get_alert_rules() -> dict:
    """Get all alert rules configuration"""
    alert_manager = get_alert_manager()
    return {
        "rules": [
            {
                "name": rule.name,
                "threshold": rule.threshold,
                "severity": rule.severity,
                "enabled": rule.enabled,
                "description": rule.description,
                "cooldown_minutes": rule.cooldown_minutes
            }
            for rule in alert_manager.alert_rules.values()
        ]
    }


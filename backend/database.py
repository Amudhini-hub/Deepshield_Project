from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker
import logging
import os

from backend.config.config import get_config

logger = logging.getLogger(__name__)

engine = None

def get_engine():
    """Get database engine with runtime config loading"""
    global engine
    config = get_config()  # Reload config at runtime
    database_url = config.DATABASE_URL
    connect_args = {}

    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    elif database_url.startswith("postgresql"):
        connect_args["connect_timeout"] = 10

    engine = create_engine(
        database_url,
        future=True,
        echo=config.DATABASE_ECHO,
        pool_size=config.DATABASE_POOL_SIZE,
        max_overflow=config.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args=connect_args,
    )
    return engine

# Create engine lazily
engine = get_engine()

def get_sessionmaker():
    """Get sessionmaker with current engine"""
    return sessionmaker(bind=get_engine(), expire_on_commit=False, class_=Session)

SessionLocal = get_sessionmaker()
Base = declarative_base()


def get_db() -> Session:
    """Dependency for FastAPI to get database session"""
    db = get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()


def init_db() -> bool:
    """Initialize database - create all tables"""
    logger.info("Initializing database...")
    try:
        # Reload config to ensure we have the latest settings
        config = get_config()
        engine = get_engine()
        from backend.models import Base as ModelsBase

        ModelsBase.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False


def health_check() -> bool:
    """Check if database is accessible"""
    try:
        # Reload config to ensure we have the latest settings
        config = get_config()
        engine = get_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database health check passed")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def drop_db() -> bool:
    """Drop all tables - USE WITH CAUTION"""
    logger.warning("Dropping all database tables...")
    try:
        from backend.models import Base as ModelsBase
        
        ModelsBase.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped")
        return True
    except Exception as e:
        logger.error(f"Error dropping database: {e}")
        return False

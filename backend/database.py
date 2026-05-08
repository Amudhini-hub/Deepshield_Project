import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from backend.config.config import get_config

logger = logging.getLogger(__name__)
config = get_config()

# Build engine kwargs based on database type
engine_kwargs = {
    "future": True,
    "echo": config.DATABASE_ECHO,
}

# Add connection args
if config.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = config.DATABASE_POOL_SIZE
    engine_kwargs["max_overflow"] = config.DATABASE_MAX_OVERFLOW
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 3600
    engine_kwargs["connect_args"] = {"connect_timeout": 10}

engine = create_engine(config.DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
Base = declarative_base()


def get_db() -> Session:
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> bool:
    """Initialize database - create all tables"""
    logger.info("Initializing database...")
    try:
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

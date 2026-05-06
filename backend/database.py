from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker
import logging

from backend.config.config import get_config

logger = logging.getLogger(__name__)
config = get_config()

engine = create_engine(
    config.DATABASE_URL,
    future=True,
    echo=config.DATABASE_ECHO,
    pool_size=config.DATABASE_POOL_SIZE,
    max_overflow=config.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,           # Verify connections are valid
    pool_recycle=3600,            # Recycle connections after 1 hour
    connect_args={"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {"connect_timeout": 10}
)

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

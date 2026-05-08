"""
Pytest configuration and fixtures for DeepShield tests
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set up test environment
os.environ.setdefault("USE_SQLITE_RUNTIME", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    return engine


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create test database session"""
    TestingSessionLocal = sessionmaker(
        bind=test_db_engine,
        expire_on_commit=False,
    )
    
    # Create tables
    from backend.models import Base
    Base.metadata.create_all(bind=test_db_engine)
    
    session = TestingSessionLocal()
    yield session
    session.close()
    
    # Drop tables after test
    Base.metadata.drop_all(bind=test_db_engine)

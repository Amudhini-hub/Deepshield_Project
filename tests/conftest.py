"""
Pytest configuration and fixtures for DeepShield tests
"""
import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up test environment BEFORE importing any backend modules
# Use file-based SQLite for testing (not :memory: as it creates separate DB per connection)
os.environ["USE_SQLITE_RUNTIME"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest"
os.environ["DATABASE_URL"] = "sqlite:///test_deepshield.db"
os.environ["DEBUG"] = "true"
os.environ["DATABASE_ECHO"] = "false"

import pytest
from sqlalchemy import inspect as sqlalchemy_inspect
from fastapi.testclient import TestClient

# Import backend modules AFTER env vars are set
# backend.database should now create engine with test database URL
import backend.database
from backend.models import Base
from backend.database import get_db
from backend.main import app

# Verify the engine is using our test database
assert "test_deepshield.db" in backend.database.config.DATABASE_URL, \
    f"Wrong DATABASE_URL: {backend.database.config.DATABASE_URL}"

test_engine = backend.database.engine


def override_get_db():
    """Override get_db dependency for testing"""
    try:
        db = backend.database.SessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """Create test database tables once per session"""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Verify tables were created
    tables = sqlalchemy_inspect(test_engine).get_table_names()
    assert 'users' in tables, f"Tables not created. Found: {tables}"
    print(f"\n✓ Test database initialized with tables: {tables}")
    
    yield
    
    # Clean up after all tests
    Base.metadata.drop_all(bind=test_engine)
    
    # Delete test database file
    from pathlib import Path
    test_db_path = Path("test_deepshield.db")
    if test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture
def client():
    """Create test client for API tests"""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create test database session"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = backend.database.SessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

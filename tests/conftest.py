"""
Pytest configuration for DeepShield tests
"""

import os
from pathlib import Path

import pytest

# Clean up test database file if it exists
test_db = Path("test.db")
if test_db.exists():
    test_db.unlink()

# Set test environment — must happen before any backend imports
os.environ["PYTEST_RUNNING"] = "true"  # disables rate limiting middleware
os.environ.setdefault("USE_SQLITE_RUNTIME", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

# Must import backend AFTER env vars are set
from sqlalchemy import create_engine, inspect

from backend.database import engine as db_engine
from backend.models import Base


# Create tables before tests run
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create database tables before running tests"""
    # Create all tables using SQLAlchemy ORM
    Base.metadata.create_all(bind=db_engine)

    # Verify tables were created
    inspector = inspect(db_engine)
    tables = inspector.get_table_names()

    if "users" not in tables:
        raise RuntimeError(f"Failed to create tables. Found: {tables}")

    print(f"\n✓ Database initialized with tables: {tables}")

    yield

    # Cleanup
    Base.metadata.drop_all(bind=db_engine)

    # Close all connections before deleting the file
    db_engine.dispose()

    test_db = Path("test.db")
    if test_db.exists():
        try:
            test_db.unlink()
        except (PermissionError, OSError):
            # Ignore errors if file is still in use
            pass


@pytest.fixture
def client():
    """HTTP test client for API tests that need it as a fixture parameter."""
    from fastapi.testclient import TestClient

    from backend.main import app

    with TestClient(app) as c:
        yield c

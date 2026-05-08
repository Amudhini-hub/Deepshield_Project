"""
Pytest configuration for DeepShield tests
"""
import os
import pytest
from pathlib import Path

# Clean up test database file if it exists
test_db = Path("test.db")
if test_db.exists():
    test_db.unlink()

# Set test environment
os.environ.setdefault("PYTEST_RUNNING", "true")
os.environ.setdefault("USE_SQLITE_RUNTIME", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

# Must import backend AFTER env vars are set
from sqlalchemy import inspect, create_engine
from backend.models import Base
from backend.database import engine as db_engine

# Create tables before tests run
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create database tables before running tests"""
    # Create all tables using SQLAlchemy ORM
    Base.metadata.create_all(bind=db_engine)
    
    # Verify tables were created
    inspector = inspect(db_engine)
    tables = inspector.get_table_names()
    
    if 'users' not in tables:
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

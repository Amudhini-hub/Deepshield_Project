#!/usr/bin/env python3
"""
Database Initialization Script
Creates all tables and optionally seeds sample data
"""

import sys
import os
from pathlib import Path

# Set environment variables before importing anything
if "--sqlite" in sys.argv or not any(arg.startswith("--postgres") for arg in sys.argv):
    os.environ["USE_SQLITE"] = "True"
    print("🔄 Using SQLite database for development...")

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.database import init_db, health_check, drop_db
from backend.database_storage import db_store
from backend.services.authentication import get_password_hash

def main():
    print("🔄 Initializing Deepshield Database...")

    try:
        # Check database connection
        print("🔍 Checking database connection...")
        if not health_check():
            print("❌ Database connection failed!")
            print("   Please ensure PostgreSQL is running and environment variables are set:")
            print("   - DATABASE_URL or (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)")
            return False

        print("✅ Database connection successful!")

        # Create tables
        print("📋 Creating database tables...")
        init_db()
        print("✅ Tables created successfully!")

        # Optional: Seed sample data
        if "--seed" in sys.argv:
            print("🌱 Seeding sample data...")
            seed_sample_data()
            print("✅ Sample data seeded!")

        print("🎉 Database initialization complete!")
        return True

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def seed_sample_data():
    """Create sample users and data for testing"""
    try:
        # Create admin user
        admin_email = "admin@deepshield.com"
        admin_password = "admin123"

        existing = db_store.get_user_by_email(admin_email)
        if not existing:
            admin_user = db_store.create_user(admin_email, get_password_hash(admin_password))
            print(f"   Created admin user: {admin_email} (ID: {admin_user.id})")
        else:
            print(f"   Admin user already exists: {admin_email}")

        # Create test user
        test_email = "test@example.com"
        test_password = "test123"

        existing = db_store.get_user_by_email(test_email)
        if not existing:
            test_user = db_store.create_user(test_email, get_password_hash(test_password))
            print(f"   Created test user: {test_email} (ID: {test_user.id})")
        else:
            print(f"   Test user already exists: {test_email}")

    except Exception as e:
        print(f"   ❌ Error seeding data: {e}")

def reset_database():
    """Drop all tables and recreate (DANGER: destroys all data)"""
    if "--reset" in sys.argv:
        print("⚠️  WARNING: This will destroy all data!")
        confirm = input("Type 'YES' to confirm: ")
        if confirm == "YES":
            print("🔄 Dropping all tables...")
            drop_db()
            print("✅ All tables dropped!")
            return True
        else:
            print("❌ Reset cancelled!")
            return False
    return False

if __name__ == "__main__":
    # Handle reset command
    if "--reset" in sys.argv:
        if reset_database():
            # After reset, initialize again
            main()
        sys.exit(0)

    # Normal initialization
    success = main()
    sys.exit(0 if success else 1)
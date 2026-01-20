#!/usr/bin/env python3
"""
Migration runner script for Deficit Bot.

This script runs Alembic migrations programmatically.
Used by Docker container on startup.
"""
import os
import sys
from alembic import command
from alembic.config import Config


def run_migrations():
    """Run all pending database migrations."""
    # Get the directory where this script is located
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Create Alembic config
    alembic_ini = os.path.join(base_dir, 'alembic.ini')
    config = Config(alembic_ini)

    # Set the script location
    config.set_main_option('script_location', os.path.join(base_dir, 'alembic'))

    # Get database path from environment
    db_path = os.getenv('DB_PATH', './data/deficit.db')

    # Ensure data directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"✅ Created database directory: {db_dir}")

    # Set database URL
    database_url = f"sqlite:///{db_path}"
    config.set_main_option('sqlalchemy.url', database_url)

    print(f"🔄 Running database migrations...")
    print(f"   Database: {db_path}")

    try:
        # Run migrations to latest version
        command.upgrade(config, "head")
        print("✅ Database migrations completed successfully")
        return 0
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_migrations())

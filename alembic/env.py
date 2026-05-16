import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Ensure the project root (where `backend/` lives) is on sys.path so that
# `from backend.models import Base` resolves regardless of where alembic is invoked.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.models import Base  # noqa: E402

# Alembic Config object — gives access to values in alembic.ini.
config = context.config

# Wire up Python logging from alembic.ini if a config file is present.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    """
    Return the database URL for migrations.

    Priority:
      1. DATABASE_URL environment variable
      2. sqlalchemy.url from alembic.ini (fallback placeholder)

    Normalises the legacy postgres:// scheme to postgresql:// required by
    SQLAlchemy 2.x.
    """
    url = os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url", "")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (emits SQL to stdout)."""
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    ini_section = dict(config.get_section(config.config_ini_section) or {})
    ini_section["sqlalchemy.url"] = get_url()

    # NullPool is correct for migration scripts — no need to keep connections
    # alive between statements.
    connectable = engine_from_config(
        ini_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Emit a BEGIN so each migration runs in a transaction that can be
            # rolled back on failure.
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

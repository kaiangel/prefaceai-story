"""Alembic env.py — synchronous migration runner (pymysql driver)

Strategy: Method A — use synchronous pymysql driver for migrations.
Migrations are one-shot CLI commands; async is unnecessary here.

- DATABASE_URL from app.config.settings (reads from .env)
- asyncmy/aiomysql driver replaced with pymysql for sync execution
- target_metadata from app.database.Base (all models registered via app.models import)
"""

import re
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ── Alembic config object (gives access to alembic.ini values) ───────────────
config = context.config

# ── Logging ───────────────────────────────────────────────────────────────────
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Import models so SQLAlchemy metadata is fully populated ──────────────────
# Importing app.models registers every ORM class against Base.metadata.
# This is required for --autogenerate to detect table changes correctly.
from app.database import Base  # noqa: E402
import app.models  # noqa: E402, F401  (side-effect import: registers all models)

target_metadata = Base.metadata


# ── Build a synchronous DATABASE_URL from app settings ───────────────────────
def _get_sync_url() -> str:
    """Convert async DATABASE_URL (asyncmy/aiomysql) → pymysql for sync migrations."""
    from app.config import settings  # lazy import to avoid circular deps at module load

    url = settings.DATABASE_URL
    # Replace async drivers with pymysql
    url = re.sub(r"mysql\+(asyncmy|aiomysql)://", "mysql+pymysql://", url)
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no live DB connection needed).

    This mode emits SQL to stdout/file rather than executing it.
    Useful for generating a migration script to review before applying.
    """
    url = _get_sync_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connects to live DB and executes DDL)."""
    # Override sqlalchemy.url in alembic config with the pymysql URL
    sync_url = _get_sync_url()
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = sync_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # no connection pooling for migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,          # detect column type changes
            compare_server_default=True,  # detect server_default changes
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

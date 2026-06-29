import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add backend root to sys.path so we can import ppt_backend
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ppt_backend.settings import settings
from ppt_backend.infrastructure.database import Base

# Import all models so they register on Base.metadata
import ppt_backend.infrastructure.models  # noqa: F401

# Alembic Config object
config = context.config

# Override sqlalchemy.url from our settings (sync URL for Alembic)
config.set_main_option("sqlalchemy.url", settings.database_url_sync)

# Set up Python loggers from the ini file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

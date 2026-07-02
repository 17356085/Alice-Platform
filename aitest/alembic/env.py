"""Alembic env — sync PostgreSQL via aitest.infra.models."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import Base + all models so metadata is populated
from aitest.infra.database import Base
import aitest.infra.models  # noqa: F401 — registers all models on Base.metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL to stdout)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (sync engine for Alembic)."""
    # Use synchronous driver for Alembic (avoid asyncpg Windows issues)
    url = config.get_main_option("sqlalchemy.url")
    sync_url = url.replace("+asyncpg", "+psycopg2") if url else url

    connectable = engine_from_config(
        {"sqlalchemy.url": sync_url or url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

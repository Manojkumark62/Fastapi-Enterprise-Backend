"""
Alembic migration environment.

Two things are wired to the actual app here, not left as scaffold defaults:
1. sqlalchemy.url is pulled from app.core.config.settings.DATABASE_URL at
   runtime, so migrations always run against whatever .env points to —
   there's no separate URL to keep in sync inside alembic.ini.
2. target_metadata is app.database.base.Base.metadata, with app.models
   imported first so every model's table is registered on it before
   autogenerate introspects it. Skipping that import is the single most
   common reason `alembic revision --autogenerate` silently produces an
   empty migration.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import every model so Base.metadata is fully populated before
# autogenerate compares it against the live database schema.
from models import * # noqa: F401
from core.config import settings
from database.base import Base

config = context.config

# Override whatever sqlalchemy.url is in alembic.ini with the real,
# environment-driven URL. This is the one line that makes `alembic
# upgrade head` and the running app always agree on which database
# they're talking to.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout without a live DB connection (`alembic upgrade head --sql`)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # detect column type changes, not just add/drop
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection (the normal case)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

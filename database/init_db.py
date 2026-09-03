"""
Database initialization helpers.

In production, schema changes should ALWAYS go through Alembic
migrations (see alembic/). `init_db()` here is a dev/test convenience
for spinning up a fresh schema quickly (e.g. in the test suite's
conftest.py) without running migrations.
"""

import logging

from database.base import Base
from database.session import engine

# Import every model module so its table is registered on Base.metadata
# before create_all() is called. This import is intentionally unused
# directly — it's here for its side effect of populating the registry.
from models import *  # noqa: F401

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Create all tables from the current models. Dev/test use only."""
    logger.info("Creating database tables from metadata (dev/test mode)")
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Drop all tables. Dev/test use only — never call in production."""
    logger.warning("Dropping all database tables")
    Base.metadata.drop_all(bind=engine)

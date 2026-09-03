"""
Application-wide logging configuration.

Called once from main.py at startup. Every module in the app should use
`logging.getLogger(__name__)` rather than print() — this ensures all
output goes through the same format/handlers configured here.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

from core.config import settings
from core.structured_logging import StructuredLogFormatter

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    """
    Configure the root logger with:
      - a console handler (always on)
      - a rotating file handler (5MB per file, 5 backups)
    Log level is controlled by settings.LOG_LEVEL so it can be tuned per
    environment without code changes (e.g. DEBUG locally, INFO in prod).
    """
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    formatter = StructuredLogFormatter()

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if setup_logging() is called more than once
    # (e.g. under a test runner that imports main multiple times).
    if root_logger.handlers:
        root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        "app.log", maxBytes=5 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Quiet down noisy third-party loggers unless we're in DEBUG mode.
    if level > logging.DEBUG:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Convenience wrapper — mainly so callers don't import logging directly."""
    return logging.getLogger(name)

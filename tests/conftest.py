"""Pytest configuration for imports from the project root."""

import os
import sys
from pathlib import Path

# Set environment variables BEFORE any other imports
# These are required by core/config.py at module import time
os.environ.setdefault("SECRET_KEY", "test-secret-key-must-be-at-least-32-characters-long-for-testing!")
os.environ.setdefault("DATABASE_URL", "mysql+pymysql://root:testpassword@127.0.0.1:3306/test_db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """Pytest hook for additional configuration (already set above)."""
    pass

"""Pytest configuration for imports from the project root."""

import sys
import os
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """Configure test environment before any test collection.
    
    This hook runs before pytest collects tests and before any module imports
    that might instantiate settings. It ensures environment variables required
    by core.config.Settings are available at module import time.
    """
    os.environ.setdefault("SECRET_KEY", "test-secret-key-must-be-at-least-32-characters-long-for-testing!")
    os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

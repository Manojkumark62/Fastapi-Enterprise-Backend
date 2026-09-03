"""Structured logging with context fields (Module 10)."""

import logging
import json
from contextvars import ContextVar
from typing import Any

# Context variables
_request_id: ContextVar[str] = ContextVar("request_id", default="")
_user_id: ContextVar[int | None] = ContextVar("user_id", default=None)
_entity_type: ContextVar[str] = ContextVar("entity_type", default="")
_entity_id: ContextVar[int | None] = ContextVar("entity_id", default=None)


class StructuredLogFormatter(logging.Formatter):
    """Format logs as structured JSON with context fields."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": _request_id.get(),
            "user_id": _user_id.get(),
            "entity_type": _entity_type.get(),
            "entity_id": _entity_id.get(),
        }
        
        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v}
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def set_request_id(request_id: str) -> None:
    """Set request ID in context."""
    _request_id.set(request_id)


def set_user_id(user_id: int | None) -> None:
    """Set user ID in context."""
    _user_id.set(user_id)


def set_entity_context(entity_type: str, entity_id: int | None = None) -> None:
    """Set entity type and ID in context."""
    _entity_type.set(entity_type)
    _entity_id.set(entity_id)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with structured formatting."""
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    formatter = StructuredLogFormatter()
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

"""
Password strength policy (Module 28 — Account Security).

A plain function rather than a class: it's called from Pydantic
validators in schemas/auth.py, so it needs to be cheap to import and
raise ValueError directly (which Pydantic converts into a 422 response
automatically — no exception translation needed here).
"""

import re

MIN_LENGTH = 8


def validate_password_strength(password: str) -> None:
    """
    Raises ValueError with a specific, user-facing message on the first
    rule violated. Deliberately checks length first since every other
    check assumes a minimum length to even be meaningful.
    """
    if len(password) < MIN_LENGTH:
        raise ValueError(f"Password must be at least {MIN_LENGTH} characters long")

    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")

    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]/~`]", password):
        raise ValueError("Password must contain at least one special character")

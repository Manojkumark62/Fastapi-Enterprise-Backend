"""Extensible password policy validation (Module 15)."""

from abc import ABC, abstractmethod
import re
from typing import list


class PasswordValidator(ABC):
    """Base class for password validation policies."""

    @abstractmethod
    def validate(self, password: str) -> tuple[bool, str | None]:
        """
        Validate a password.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass


class MinimumLengthValidator(PasswordValidator):
    """Enforce minimum password length."""

    def __init__(self, min_length: int = 8):
        self.min_length = min_length

    def validate(self, password: str) -> tuple[bool, str | None]:
        if len(password) < self.min_length:
            return False, f"Password must be at least {self.min_length} characters long"
        return True, None


class ComplexityValidator(PasswordValidator):
    """Enforce password complexity (uppercase, lowercase, digit, special char)."""

    def validate(self, password: str) -> tuple[bool, str | None]:
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit"
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character"
        return True, None


class BlacklistValidator(PasswordValidator):
    """Check password against a blacklist."""

    def __init__(self, blacklist: list[str] | None = None):
        self.blacklist = blacklist or [
            "password", "123456", "qwerty", "abc123", "password123",
            "admin", "letmein", "welcome",
        ]

    def validate(self, password: str) -> tuple[bool, str | None]:
        if password.lower() in self.blacklist:
            return False, "Password is too common"
        return True, None


class PasswordPolicyValidator:
    """Composite validator that runs multiple policy validators."""

    def __init__(self, validators: list[PasswordValidator] | None = None):
        self.validators = validators or [
            MinimumLengthValidator(8),
            ComplexityValidator(),
            BlacklistValidator(),
        ]

    def validate(self, password: str) -> tuple[bool, str | None]:
        """Run all validators and return first error, or (True, None) if all pass."""
        for validator in self.validators:
            is_valid, error = validator.validate(password)
            if not is_valid:
                return False, error
        return True, None

    def add_validator(self, validator: PasswordValidator) -> None:
        """Add a custom validator to the policy."""
        self.validators.append(validator)


# Default policy instance
default_policy = PasswordPolicyValidator()

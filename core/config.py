"""
Centralized application configuration.

All environment-dependent values are declared here as typed fields and
loaded from a .env file (or real environment variables in production).
Nothing else in the codebase should call os.environ directly — import
`settings` from this module instead.
"""

from functools import lru_cache
from typing import Dict, List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- General ---
    PROJECT_NAME: str = "FastAPI Enterprise Backend"
    API_V1_PREFIX: str = "/api/v1"
    API_V2_PREFIX: str = "/api/v2"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = False
    TRUSTED_PROXY_HEADERS: bool = False

    # --- Security / Auth ---
    SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Database ---
    DATABASE_URL: str

    # --- Redis / Cache ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_DEFAULT_TTL_SECONDS: int = 300

    # --- CORS ---
    # Typed as Union[str, List[str]] (not just List[str]) so pydantic-settings
    # does not attempt to JSON-decode a plain "a,b,c" .env value before this
    # validator gets a chance to split it.
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, v):
        if isinstance(v, str):
            if v.startswith("["):
                return v  # already JSON — let pydantic parse it normally
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # --- Rate limiting ---
    RATE_LIMIT_PER_MINUTE: int = 5

    # --- Email (used by services/email_service.py) ---
    # Use a real Gmail App Password here when testing actual email delivery.
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "manojkumarkancharla143@gmail.com"
    SMTP_PASSWORD: str = "rzthzmhxorbvubtc"
    EMAIL_FROM: str = "manojkumarkancharla143@gmail.com"

    # --- File uploads ---
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # --- Pagination ---
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    # --- Webhooks ---
    # Map the event source (for example, "stripe") to its delivery endpoint.
    WEBHOOK_URLS: Dict[str, str] = {}
    WEBHOOK_SECRETS: Dict[str, str] = {}
    WEBHOOK_TIMEOUT_SECONDS: float = 10.0
    WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS: int = 300
    EXTERNAL_HEALTH_URL: str | None = None


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings accessor. Using lru_cache means the .env file is
    parsed exactly once per process, not on every import.
    """
    return Settings()


settings = get_settings()

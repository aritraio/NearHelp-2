"""Typed application settings, loaded from environment / .env.

Every variable NearHelp reads lives here and in the root .env.example —
the two files must stay in sync (see BLUEPRINT.md §6 "Secrets").
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # .env may carry vars for other tools (POSTGRES_*, future keys) — don't explode on them.
        extra="ignore",
    )

    env: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://nearhelp:nearhelp@localhost:5432/nearhelp"
    database_url_sync: str = "postgresql+psycopg://nearhelp:nearhelp@localhost:5432/nearhelp"
    redis_url: str = "redis://localhost:6379/0"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # --- Auth (Phase 1) ------------------------------------------------------
    # HS256 is deliberate: one issuing service (this backend) and one audience.
    # Swap to RS256 only if a second service must verify tokens (tech-stack.md ADR-7).
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_ttl_min: int = 15
    refresh_token_ttl_days: int = 7

    # --- Rate limits (Phase 1) ------------------------------------------------
    rate_limit_per_min: int = 100  # authenticated requests per user
    auth_rate_limit_per_min: int = 30  # unauthenticated /api/auth/* per IP
    sos_daily_limit: int = 10  # consumed by the SOS engine in Phase 2

    # --- Certificates (Phase 1) -----------------------------------------------
    certificate_dir: str = "./data/certificates"


@lru_cache
def get_settings() -> Settings:
    return Settings()

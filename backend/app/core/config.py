"""
Central place for all environment/configuration values.

Why this file exists on its own:
Every real production incident caused by "it worked on my machine" traces
back to config values scattered across the codebase. Keeping every setting
in ONE place means there is exactly one place to check when something is
misconfigured, and exactly one place to update per environment (dev/staging/prod).

Never hardcode secrets, API keys, or DB URLs anywhere else in the codebase.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"

    APP_DATABASE_URL: str = "postgresql://user:password@localhost:5432/querynetic"

    LLM_PROVIDER: str = "groq"
    LLM_API_KEY: str = ""

    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"

    ENCRYPTION_KEY: str = ""

    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
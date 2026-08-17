"""
Central place for all environment/configuration values.

Why this file exists on its own:
Every real production incident caused by "it worked on my machine" traces
back to config values scattered across the codebase. Keeping every setting
in ONE place means there is exactly one place to check when something is
misconfigured, and exactly one place to update per environment (dev/staging/prod).

Never hardcode secrets, API keys, or DB URLs anywhere else in the codebase.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "development"

    # Querynetic's own app database (stores users, chats, orgs)
    APP_DATABASE_URL: str = "postgresql://user:password@localhost:5432/querynetic"

    # LLM provider config (pluggable — don't hardcode a single vendor)
    LLM_PROVIDER: str = "groq"
    LLM_API_KEY: str = ""

    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Fernet key for encrypting stored database connection strings. Generate
    # one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    ENCRYPTION_KEY: str = ""

    # Used to encrypt/decrypt stored database connection strings. Must be a
    # valid Fernet key — generate one with:
    #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    ENCRYPTION_KEY: str = ""

    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"


settings = Settings()
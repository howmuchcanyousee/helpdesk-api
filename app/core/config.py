from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Helpdesk API"
    app_env: str = "development"
    debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    database_url: str
    secret_key: str = Field(min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        hide_input_in_errors=True,
    )

    @field_validator("secret_key")
    @classmethod
    def reject_placeholder_secret(cls, value: str) -> str:
        if value.startswith("replace_"):
            raise ValueError("SECRET_KEY must be replaced with a random value")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

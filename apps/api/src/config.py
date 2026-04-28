from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve repo root regardless of where the server is launched from
_REPO_ROOT = Path(__file__).parent.parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str
    openai_api_key: str
    anilist_api_url: str = "https://graphql.anilist.co"
    logfire_token: str | None = None


settings = Settings()

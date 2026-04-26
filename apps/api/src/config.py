from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve repo root regardless of where the server is launched from
_REPO_ROOT = Path(__file__).parent.parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str
    groq_api_key: str
    groq_base_url: str = "https://api.groq.com/openai/v1"
    anilist_api_url: str = "https://graphql.anilist.co"


settings = Settings()

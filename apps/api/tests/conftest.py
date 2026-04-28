import os

# Must be set before src.* is imported so Settings() doesn't fail at collection time.
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("LOGFIRE_TOKEN", "")

"""AgentDAC Backend configuration."""

import os

from pydantic_settings import BaseSettings


class ServerSettings(BaseSettings):
    """FastAPI server runtime settings."""

    model_config = {"env_prefix": "AGENTDAC_", "extra": "ignore"}

    app_name: str = "AgentDAC Ingestion and Visualization API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database connection URL (defaults to async SQLite for local/test, PostgreSQL for prod)
    database_url: str = os.getenv(
        "AGENTDAC_DATABASE_URL",
        os.getenv("AOG_DATABASE_URL", "sqlite+aiosqlite:///./aog.db"),
    )

    api_key: str | None = os.getenv("AGENTDAC_API_KEY", os.getenv("AOG_API_KEY"))
    cors_origins: list[str] = ["*"]
    max_payload_bytes: int = 1_000_000

    def get_async_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = ServerSettings()


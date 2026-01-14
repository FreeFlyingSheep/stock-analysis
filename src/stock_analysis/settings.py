"""Settings for the stock analysis application."""

from functools import cached_property, lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from pydantic_settings.sources.types import DotenvType


class Settings(BaseSettings):
    """Application settings.

    This class contains all configuration settings for the stock analysis
    application including database connection details and server configuration.
    """

    model_config = SettingsConfigDict(
        env_file=".env" if Path(".env").exists() else None,
        env_file_encoding="utf-8",
        frozen=True,
        extra="ignore",
    )

    database_user: str
    """Database user."""
    database_password: str
    """Database password."""
    database_host: str
    """Database host."""
    database_port: int
    """Database port."""
    database_db: str
    """Database name."""

    rule_file_path: str
    """Path to the rule configuration file."""
    debug: bool
    """Enable or disable debug mode."""
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    """Logging level for the application."""
    log_file: str
    """File path for the log file."""
    host: str
    """Host address to run the application on."""
    port: int
    """Port to run the application on."""

    worker_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    """Logging level for worker processes."""
    worker_log_file: str
    """File path for the worker log file."""
    batch_size: int
    """Batch size for processing data."""
    max_concurrent_tasks: int
    """Maximum number of concurrent tasks."""

    hf_token: str | None
    """Hugging Face authentication token."""
    vllm_model: str
    """Model name to be used by the VLLM server."""
    vllm_host: str
    """VLLM server host address."""
    vllm_port: int
    """Port number for the VLLM server."""

    ui_host: str
    """Host address for the UI to bind to."""
    ui_port: int
    """Port number for the UI to listen on."""

    @cached_property
    def database_url(self) -> str:
        """Construct the PostgreSQL database connection URL.

        Returns:
            PostgreSQL connection string in psycopg format.
        """
        return (
            f"postgresql+psycopg://{self.database_user}:"
            f"{self.database_password}@{self.database_host}:"
            f"{self.database_port}/{self.database_db}"
        )


@lru_cache(maxsize=1)
def get_settings(env_file: DotenvType | None = None) -> Settings:
    """Get or create the application settings instance.

    Args:
        env_file: Optional environment file path. If None, uses default .env file.

    Returns:
        Settings instance with configuration from environment.
    """
    if env_file is not None:
        return Settings(_env_file=env_file)  # type: ignore[call-arg]
    return Settings()  # type: ignore[call-arg]

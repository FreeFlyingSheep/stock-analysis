"""Settings for the stock analysis application."""

from functools import cached_property, lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Self

from pydantic import (
    SecretStr,  # noqa: TC002
    model_validator,
)
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

    no_log_file: bool = False
    """Flag to disable logging to a file."""

    database_user: str
    """Database user."""
    database_password: SecretStr
    """Database password."""
    database_host: str
    """Database host."""
    database_port: int
    """Database port."""
    database_db: str
    """Database name."""

    minio_host: str
    """MinIO host."""
    minio_port: int
    """MinIO port."""
    minio_user: str
    """MinIO root user."""
    minio_password: SecretStr
    """MinIO root password."""
    minio_bucket_prefix: str
    """Prefix for MinIO buckets."""
    minio_secure: bool
    """Use secure connection for MinIO."""

    redis_host: str
    """Redis host."""
    redis_port: int
    """Redis port."""
    redis_prefix: str
    """Prefix for Redis keys."""

    config_dir: str
    """Directory for configuration files."""
    rule_file_path: str
    """Path to the rule configuration file."""
    debug: bool
    """Enable or disable debug mode."""
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    """Logging level for the backend."""
    log_file: str | None
    """File path for the log file."""
    backend_host: str
    """Host address to run the backend on."""
    backend_port: int
    """Port to run the backend on."""

    worker_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    """Logging level for worker processes."""
    worker_log_file: str | None
    """File path for the worker log file."""
    batch_size: int
    """Batch size for processing data."""
    max_concurrent_tasks: int
    """Maximum number of concurrent tasks."""

    use_llm: bool
    """Flag to enable or disable the use of online LLM for LLM tasks."""
    llm_api_key: SecretStr | None = None
    """API key for the online LLM service."""
    llm_server_base_url: str | None = None
    """Base URL for the online LLM server."""
    llm_model: str | None = None
    """LLM model name."""
    llm_embedding_model: str | None = None
    """LLM embedding model name."""

    mcp_host: str
    """Host address for the MCP server."""
    mcp_port: int
    """Port for the MCP server."""

    @model_validator(mode="after")
    def _check_llm_fields(self) -> Self:
        if self.use_llm:
            missing: list[str] = [
                name
                for name in (
                    "llm_api_key",
                    "llm_server_base_url",
                    "llm_model",
                    "llm_embedding_model",
                    "mcp_host",
                    "mcp_port",
                )
                if getattr(self, name) in (None, "")
            ]
            if missing:
                msg: str = f"LLM is enabled, but missing fields: {', '.join(missing)}"
                raise ValueError(msg)
        return self

    @cached_property
    def database_url_with_psycopg(self) -> str:
        """Construct the PostgreSQL database connection URL.

        Returns:
            PostgreSQL connection string in psycopg format.
        """
        return (
            f"postgresql+psycopg://{self.database_user}:"
            f"{self.database_password.get_secret_value()}@{self.database_host}:"
            f"{self.database_port}/{self.database_db}"
        )

    @cached_property
    def database_url(self) -> str:
        """Construct the database connection URL.

        Returns:
            Database connection string.
        """
        return (
            f"postgresql://{self.database_user}:"
            f"{self.database_password.get_secret_value()}@{self.database_host}:"
            f"{self.database_port}/{self.database_db}"
        )

    @cached_property
    def minio_endpoint(self) -> str:
        """Construct the MinIO server endpoint.

        Returns:
            Endpoint for the MinIO server.
        """
        return f"{self.minio_host}:{self.minio_port}"

    @cached_property
    def minio_bucket_raw(self) -> str:
        """Construct the raw MinIO bucket name.

        Returns:
            Raw bucket name for MinIO.
        """
        return f"{self.minio_bucket_prefix}raw"

    @cached_property
    def minio_bucket_processed(self) -> str:
        """Construct the processed MinIO bucket name.

        Returns:
            Processed bucket name for MinIO.
        """
        return f"{self.minio_bucket_prefix}processed"

    @cached_property
    def api_url(self) -> str:
        """Construct the API base URL.

        Returns:
            Base URL for the backend API.
        """
        return f"http://{self.backend_host}:{self.backend_port}"

    @cached_property
    def mcp_url(self) -> str:
        """Construct the MCP server URL.

        Returns:
            URL for the MCP server.
        """
        return f"http://{self.mcp_host}:{self.mcp_port}/mcp"


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

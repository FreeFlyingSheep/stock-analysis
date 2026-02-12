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

    Attributes:
        no_log_file: Flag to disable logging to a file.
        database_user: Database user.
        database_password: Database password.
        database_host: Database host.
        database_port: Database port.
        database_db: Database name.
        minio_host: MinIO host.
        minio_port: MinIO port.
        minio_user: MinIO root user.
        minio_password: MinIO root password.
        minio_bucket_prefix: Prefix for MinIO buckets.
        minio_secure: Use secure connection for MinIO.
        redis_host: Redis host.
        redis_port: Redis port.
        redis_prefix: Prefix for Redis keys.
        config_dir: Directory for CNInfo configuration files.
        rule_file_path: Path to the rule configuration file.
        prompts_dir: Directory for prompt templates.
        debug: Enable or disable debug mode.
        log_level: Logging level for the backend.
        log_file: File path for the log file.
        backend_host: Host address to run the backend on.
        backend_port: Port to run the backend on.
        worker_log_level: Logging level for worker processes.
        worker_log_file: File path for the worker log file.
        batch_size: Batch size for processing data.
        max_concurrent_tasks: Maximum number of concurrent tasks.
        use_llm: Flag to enable or disable the use of online LLM for LLM tasks.
        llm_api_key: API key for the online LLM service.
        llm_server_base_url: Base URL for the online LLM server.
        llm_model: LLM model name.
        llm_embedding_model: LLM embedding model name.
        llm_embedding_dimension: LLM embedding dimension.
        mcp_host: Host address for the MCP server.
        mcp_port: Port for the MCP server.
        monitoring_host: Host address for the monitoring server.
        monitoring_port: Port for the monitoring server.
    """

    model_config = SettingsConfigDict(
        env_file=".env" if Path(".env").exists() else None,
        env_file_encoding="utf-8",
        frozen=True,
        extra="ignore",
    )

    no_log_file: bool = False

    database_user: str
    database_password: SecretStr
    database_host: str
    database_port: int
    database_db: str

    minio_host: str
    minio_port: int
    minio_user: str
    minio_password: SecretStr
    minio_bucket_prefix: str
    minio_secure: bool

    redis_host: str
    redis_port: int
    redis_prefix: str

    config_dir: str
    rule_file_path: str
    prompts_dir: str
    debug: bool
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    log_file: str | None
    backend_host: str
    backend_port: int

    worker_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    worker_log_file: str | None
    batch_size: int
    max_concurrent_tasks: int

    use_llm: bool
    llm_api_key: SecretStr | None = None
    llm_server_base_url: str | None = None
    llm_model: str | None = None
    llm_embedding_model: str | None = None
    llm_embedding_dimension: int | None = None

    mcp_host: str
    mcp_port: int

    monitoring_host: str
    monitoring_port: int

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
                    "llm_embedding_dimension",
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

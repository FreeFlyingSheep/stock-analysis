"""Settings for the stock analysis application."""

from functools import cached_property, lru_cache
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
        env_file=".env", env_file_encoding="utf-8", frozen=True
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

    @cached_property
    def database_url(self) -> str:
        """Construct the database URL.

        Returns:
            str: PostgreSQL database connection URL.
        """
        return (
            f"postgresql+psycopg://{self.database_user}:"
            f"{self.database_password}@{self.database_host}:"
            f"{self.database_port}/{self.database_db}"
        )


@lru_cache(maxsize=1)
def get_settings(env_file: DotenvType | None = None) -> Settings:
    """Get application settings.

    Args:
        env_file: Optional environment file path. If None, uses default .env file.

    Returns:
        Settings: Application settings instance.
    """
    if env_file is not None:
        return Settings(_env_file=env_file)  # type: ignore[call-arg]
    return Settings()  # type: ignore[call-arg]

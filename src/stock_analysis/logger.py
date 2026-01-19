"""Logging setup for stock analysis application."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from stock_analysis.settings import Settings, get_settings

if TYPE_CHECKING:
    from stock_analysis.settings import Settings


def _create_log_dir(log_file_path: Path) -> None:
    """Create log directory and parent directories if they don't exist.

    Args:
        log_file_path: Path to the log file to create.
    """
    if not log_file_path.exists():
        log_file_path.parent.mkdir(parents=True, exist_ok=True)


def _add_file_handler(logger: logging.Logger, log_file_path: Path) -> None:
    """Add FileHandler to logger.

    Args:
        logger: Logger instance to modify.
        log_file_path: Path to the log file to handle.
    """
    file_handler = RotatingFileHandler(log_file_path, maxBytes=10**6, backupCount=5)
    file_handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(file_handler)


def get_logger(
    name: str | None = None, type_: Literal["app", "worker"] = "app"
) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: The name of the logger to retrieve. If None, the root logger is returned.
        type_: Type of logger, either "app" or "worker".

    Returns:
        Configured logger instance with file handler.
    """
    settings: Settings = get_settings()
    if type_ == "worker":
        log_level: str = settings.worker_log_level
        log_file_path: Path | None = (
            Path(settings.worker_log_file) if settings.worker_log_file else None
        )
    else:
        log_level = settings.log_level
        log_file_path = Path(settings.log_file) if settings.log_file else None

    logger: logging.Logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if settings.no_log_file or log_file_path is None:
        return logger

    _create_log_dir(log_file_path)
    _add_file_handler(logger, log_file_path)

    return logger

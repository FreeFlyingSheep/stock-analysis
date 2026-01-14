"""Logging setup for stock analysis application."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from stock_analysis.settings import Settings


def _create_log_file_if_not_exists(log_file_path: Path) -> None:
    """Create log file and parent directories if they don't exist.

    Args:
        log_file_path: Path to the log file to create.
    """
    if not log_file_path.exists():
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        log_file_path.touch()


def _add_file_handler_if_missing(logger: logging.Logger, log_file_path: Path) -> None:
    """Add FileHandler to logger if not already present.

    Args:
        logger: Logger instance to modify.
        log_file_path: Path to the log file to handle.
    """
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        file_handler = RotatingFileHandler(log_file_path, maxBytes=10**6, backupCount=5)
        file_handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)


def get_logger(name: str, type_: Literal["app", "worker"] = "app") -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: The name of the logger to retrieve.
        type_: Type of logger, either "app" or "worker".

    Returns:
        Configured logger instance with file handler.
    """
    settings: Settings = get_settings()
    if type_ == "worker":
        log_level: str = settings.worker_log_level
        log_file_path = Path(settings.worker_log_file)
    else:
        log_level = settings.log_level
        log_file_path = Path(settings.log_file)

    _create_log_file_if_not_exists(log_file_path)

    logger: logging.Logger = logging.getLogger(name)
    logger.setLevel(log_level)
    _add_file_handler_if_missing(logger, log_file_path)

    return logger


def setup_loggers(names: list[str]) -> None:
    """Set up multiple loggers with file handlers.

    Args:
        names: List of logger names to configure.
    """
    settings: Settings = get_settings()
    log_file_path = Path(settings.log_file)
    _create_log_file_if_not_exists(log_file_path)

    for name in names:
        logger: logging.Logger = logging.getLogger(name)
        logger.setLevel(settings.log_level)
        _add_file_handler_if_missing(logger, log_file_path)

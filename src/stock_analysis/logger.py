"""Logging setup for stock analysis application."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from stock_analysis.settings import Settings


def _create_log_file_if_not_exists(log_file_path: Path) -> None:
    """Create the log file and its parent directories if they do not exist.

    Args:
        log_file_path (Path): The path to the log file.
    """
    if not log_file_path.exists():
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        log_file_path.touch()


def _add_file_handler_if_missing(logger: logging.Logger, log_file_path: Path) -> None:
    """Add a FileHandler to the logger if it does not already have one.

    Args:
        logger (logging.Logger): The logger to modify.
        log_file_path (Path): The path to the log file.
    """
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger for the given name.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    settings: Settings = get_settings()
    log_file_path = Path(settings.log_file)
    _create_log_file_if_not_exists(log_file_path)

    logger: logging.Logger = logging.getLogger(name)
    logger.setLevel(settings.log_level)
    _add_file_handler_if_missing(logger, log_file_path)

    return logger


def setup_loggers(names: list[str]) -> None:
    """Set up loggers for the application.

    Args:
        names (list[str]): The names of the loggers to set up.

    Returns:
        logging.Logger: Configured logger instance.
    """
    settings: Settings = get_settings()
    log_file_path = Path(settings.log_file)
    _create_log_file_if_not_exists(log_file_path)

    for name in names:
        logger: logging.Logger = logging.getLogger(name)
        logger.setLevel(settings.log_level)
        _add_file_handler_if_missing(logger, log_file_path)

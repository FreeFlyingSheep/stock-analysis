"""Entry point for the stock analysis application."""

import logging
from typing import TYPE_CHECKING

import uvicorn

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from stock_analysis.settings import Settings


def main() -> None:
    """Run the FastAPI application with Uvicorn.

    This function initializes logging and starts the FastAPI application
    using Uvicorn with settings from the environment configuration.
    """
    settings: Settings = get_settings()

    logging.basicConfig(level=settings.log_level)

    uvicorn.run(
        "stock_analysis.routers.app:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    main()

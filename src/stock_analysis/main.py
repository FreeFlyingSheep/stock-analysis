"""Entry point for the stock analysis application."""

from typing import TYPE_CHECKING

import uvicorn

from stock_analysis.logger import get_logger
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from stock_analysis.settings import Settings


def main() -> None:
    """Run the FastAPI application with Uvicorn.

    This function initializes logging and starts the FastAPI application
    using Uvicorn with settings from the environment configuration.
    """
    get_logger()
    settings: Settings = get_settings()
    uvicorn.run(
        "stock_analysis.routers.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
    )


if __name__ == "__main__":
    main()

"""App router for stock analysis application.

Defines the FastAPI application instance and common routes, and configures
OpenAPI metadata (title, description, version, and tags).
"""

from contextlib import asynccontextmanager
from importlib.metadata import version
from typing import TYPE_CHECKING

from fastapi import FastAPI

from stock_analysis.jobs.pgqueuer import (
    close_connection,
    create_pgqueuer_with_connection,
    get_connection,
)
from stock_analysis.routers.analysis import router as analysis_router
from stock_analysis.routers.stock import router as stock_router
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from psycopg import AsyncConnection

    from stock_analysis.settings import Settings

settings: Settings = get_settings()

description: str = """
Stock Analysis API for Chinese A-share fundamental scoring and data access.

**Disclaimer: This tool is for reference and educational purposes only.**
It does not provide financial advice. Investment involves risk.
"""

tags: list[dict[str, str]] = [
    {
        "name": "stocks",
        "description": "Operations for querying stocks with filtering and pagination.",
    },
    {
        "name": "analysis",
        "description": "Operations for querying stock analysis results.",
    },
]

message: str = "Welcome to the Stock Analysis API!"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage application startup and shutdown lifecycle.

    Initializes PgQueuer connection on startup and closes it on shutdown.

    Args:
        app: FastAPI application instance.

    Yields:
        None during application running phase.
    """
    conn: AsyncConnection = await get_connection()
    app.state.pgq = await create_pgqueuer_with_connection(conn)

    yield

    await close_connection(conn)


app = FastAPI(
    debug=settings.debug,
    title="Stock Analysis API",
    description=description,
    version=version("stock-analysis"),
    openapi_tags=tags,
    lifespan=lifespan,
)
app.include_router(stock_router, tags=["stocks"])
app.include_router(analysis_router, tags=["analysis"])


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint returning a welcome message.

    Returns:
        Dict containing welcome message for the API.
    """
    return {"message": message}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Dict containing service health status.
    """
    return {"status": "ok"}

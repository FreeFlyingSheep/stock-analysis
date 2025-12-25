"""App router for stock analysis application.

Defines the FastAPI application instance and common routes, and configures
OpenAPI metadata (title, description, version, and tags).
"""

from contextlib import asynccontextmanager
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from stock_analysis.jobs.pgqueuer import (
    close_connection,
    create_pgqueuer_with_connection,
    get_connection,
)
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
    }
]

message: str = "Welcome to the Stock Analysis API!"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Lifespan context manager to handle startup and shutdown events."""
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


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    """Serve the favicon.ico file.

    Returns:
        FileResponse: HTTP response containing the favicon.ico file.
    """
    root: Path = Path(__file__).parents[3]
    return FileResponse(root / "static" / "favicon.ico")


@app.get("/")
async def root() -> JSONResponse:
    """Root endpoint returning a welcome message.

    Returns:
        JSONResponse: JSON response containing a welcome message.
    """
    return JSONResponse({"message": message})

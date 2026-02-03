"""App router for stock analysis application.

Defines the FastAPI application instance and common routes, and configures
OpenAPI metadata (title, description, version, and tags).
"""

from contextlib import asynccontextmanager
from importlib.metadata import version
from typing import TYPE_CHECKING

from fastapi import FastAPI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StreamableHttpConnection
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from minio import Minio
from psycopg_pool import AsyncConnectionPool
from redis.asyncio import ConnectionPool
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from stock_analysis.agent.graph import ChatAgent
from stock_analysis.routers.analysis import router as analysis_router
from stock_analysis.routers.chat import router as chat_router
from stock_analysis.routers.stock import router as stock_router
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
        AsyncSession,
    )

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
    {
        "name": "health",
        "description": "Health check endpoint to verify service status.",
    },
    {
        "name": "chat",
        "description": "Chat with the stock analysis agent for insights and data.",
    },
]

message: str = "Welcome to the Stock Analysis API!"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage application startup and shutdown lifecycle.

    Initializes PgQueuer connection on startup and closes it on shutdown.

    Args:
        app: FastAPI application instance.
    """
    engine: AsyncEngine = create_async_engine(
        settings.database_url_with_psycopg,
        echo=settings.debug,
    )
    async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )
    app.state.db_session = async_session

    app.state.pgq_pool = AsyncConnectionPool(
        settings.database_url, kwargs={"autocommit": True}
    )

    app.state.redis_pool = ConnectionPool(
        host=settings.redis_host, port=settings.redis_port, db=0
    )

    app.state.mc = Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_user,
        secret_key=settings.minio_password.get_secret_value(),
        secure=settings.minio_secure,
    )

    app.state.mcp = MultiServerMCPClient(
        {
            "stock-analysis": StreamableHttpConnection(
                {"transport": "streamable_http", "url": settings.mcp_url}
            )
        }
    )

    async with AsyncPostgresSaver.from_conn_string(
        settings.database_url
    ) as checkpointer:
        await checkpointer.setup()
        app.state.agent = ChatAgent(checkpointer)

        yield


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
app.include_router(chat_router, tags=["chat"])


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint returning a welcome message.

    Returns:
        Dict containing welcome message for the API.
    """
    return {"message": message}


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Dict containing service health status.
    """
    return {"status": "ok"}

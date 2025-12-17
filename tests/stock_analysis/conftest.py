from collections.abc import AsyncGenerator  # noqa: TC003
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,  # noqa: TC002
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer  # type: ignore[import-untyped]

from stock_analysis.models.base import Base
from stock_analysis.models.stock import Stock
from stock_analysis.services.database import get_db

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from fastapi import APIRouter
    from sqlalchemy.ext.asyncio import AsyncEngine


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def postgres_container() -> AsyncGenerator[PostgresContainer]:
    with PostgresContainer("postgres:18", driver="psycopg") as container:
        yield container


@pytest_asyncio.fixture(scope="session")
async def async_engine(
    postgres_container: PostgresContainer,
) -> AsyncGenerator[AsyncEngine]:
    connection_url: str = postgres_container.get_connection_url()
    engine: AsyncEngine = create_async_engine(connection_url, echo=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(
    async_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession]:
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session: async_sessionmaker[AsyncSession] = async_sessionmaker(
        async_engine,
        expire_on_commit=False,
    )
    async with session() as s:
        await s.begin()
        yield s
        await s.rollback()
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def seed_stocks(async_session: AsyncSession) -> list[Stock]:
    stocks: list[Stock] = [
        Stock(
            stock_code="000001",
            company_name="测试公司",
            classification="金融业",
            industry="银行业",
        ),
        Stock(
            stock_code="000002",
            company_name="房地产公司",
            classification="房地产",
            industry="房地产",
        ),
        Stock(
            stock_code="000003",
            company_name="科技公司",
            classification="科技",
            industry="软件",
        ),
        Stock(
            stock_code="000004",
            company_name="金融业公司",
            classification="金融业",
            industry="银行业",
        ),
    ]
    async_session.add_all(stocks)
    await async_session.flush()
    return stocks


@pytest_asyncio.fixture
async def app_factory(
    async_session: AsyncSession,
) -> Callable[[list[APIRouter]], FastAPI]:
    def make_app(routers: list[APIRouter]) -> FastAPI:
        app = FastAPI()
        for r in routers:
            app.include_router(r)

        async def override_get_db() -> AsyncGenerator[AsyncSession]:
            yield async_session

        app.dependency_overrides[get_db] = override_get_db
        return app

    return make_app


@pytest_asyncio.fixture
async def client_factory() -> Callable[[FastAPI], Awaitable[AsyncClient]]:
    async def make_client(app: FastAPI) -> AsyncClient:
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    return make_client

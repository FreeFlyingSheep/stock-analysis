from collections.abc import AsyncGenerator  # noqa: TC003
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from aiolimiter import AsyncLimiter
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, MockTransport, Response
from sqlalchemy.ext.asyncio import (
    AsyncSession,  # noqa: TC002
    async_sessionmaker,
    create_async_engine,
)
from tenacity import wait_exponential
from testcontainers.postgres import PostgresContainer  # type: ignore[import-untyped]

from stock_analysis.adaptors.cninfo import CNInfoAdaptor
from stock_analysis.models.base import Base
from stock_analysis.models.stock import Stock
from stock_analysis.services.database import get_db

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from pathlib import Path

    from fastapi import APIRouter
    from httpx import Request
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
    engine: AsyncEngine = create_async_engine(connection_url)
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


@pytest.fixture(scope="session")
def yaml_config_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    balance_sheets: str = """
api:
  id: balance_sheets
  name: 资产负债表
  request:
    method: GET
    url: https://test.api.com/balance_sheets
    params:
"""
    income_statement = """
api:
  id: income_statement
  name: 利润表
  request:
    method: GET
    url: https://test.api.com/income_statement
    params:
        stock_code:
            label: scode
            type: string
            name: 股票代码
        sign:
            label: sign
            type: integer
            value: 1
"""
    config_dir: Path = tmp_path_factory.mktemp("configs")
    balance_sheets_path: Path = config_dir / "balance_sheets.yaml"
    income_statement_path: Path = config_dir / "income_statement.yaml"
    balance_sheets_path.write_text(balance_sheets, encoding="utf-8")
    income_statement_path.write_text(income_statement, encoding="utf-8")
    return config_dir


@pytest_asyncio.fixture
async def httpx_client_factory() -> Callable[
    [int, bytes],
    Awaitable[tuple[AsyncClient, dict[str, int]]],
]:
    async def make_client(
        status_code: int,
        content: bytes,
    ) -> tuple[AsyncClient, dict[str, int]]:
        counter: dict[str, int] = {"count": 0}

        def handler(request: Request) -> Response:
            counter["count"] += 1
            return Response(
                status_code=status_code,
                content=content,
                request=request,
            )

        transport = MockTransport(handler)
        client = AsyncClient(transport=transport)
        return client, counter

    return make_client


@pytest.fixture
def async_limiter() -> AsyncLimiter:
    return AsyncLimiter(max_rate=1000, time_period=1.0)


@pytest.fixture
def wait_strategy() -> wait_exponential:
    return wait_exponential(min=1, max=2)


@pytest.fixture
def cninfo_adaptor(
    yaml_config_dir: Path, async_limiter: AsyncLimiter, wait_strategy: wait_exponential
) -> CNInfoAdaptor:
    return CNInfoAdaptor(
        config_dir=yaml_config_dir,
        timeout=2.0,
        limiter=async_limiter,
        retry_attempts=2,
        wait=wait_strategy,
    )

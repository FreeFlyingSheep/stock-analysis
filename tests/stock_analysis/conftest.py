import json
from collections.abc import AsyncGenerator  # noqa: TC003
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
import pytest_asyncio
from aiolimiter import AsyncLimiter
from fastapi import FastAPI
from fastmcp import FastMCP
from fastmcp.client import Client
from httpx import ASGITransport, AsyncClient, MockTransport, Response
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import (
    AsyncSession,  # noqa: TC002
    async_sessionmaker,
    create_async_engine,
)
from tenacity import wait_exponential
from testcontainers.minio import MinioContainer  # type: ignore[import-untyped]
from testcontainers.postgres import PostgresContainer  # type: ignore[import-untyped]
from testcontainers.redis import RedisContainer  # type: ignore[import-untyped]

from stock_analysis.adapters.cninfo import CNInfoAdapter
from stock_analysis.adapters.rule import RuleAdapter
from stock_analysis.models.analysis import Analysis
from stock_analysis.models.base import Base
from stock_analysis.models.cninfo import CNInfoAPIResponse  # noqa: F401
from stock_analysis.models.stock import Stock
from stock_analysis.models.yahoo import YahooFinanceAPIResponse  # noqa: F401
from stock_analysis.routers.analysis import router as analysis_router
from stock_analysis.routers.stock import router as stock_router
from stock_analysis.services.cache import get_redis
from stock_analysis.services.database import get_db

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Generator

    from fastapi import APIRouter
    from fastmcp.client import FastMCPTransport
    from fastmcp.server.openapi import FastMCPOpenAPI
    from httpx import Request
    from minio import Minio
    from sqlalchemy.ext.asyncio import AsyncEngine


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def postgres_container() -> AsyncGenerator[PostgresContainer]:
    with PostgresContainer("pgvector/pgvector:pg18", driver="psycopg") as container:
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


@pytest.fixture(scope="session")
def minio_container() -> Generator[MinioContainer]:
    with MinioContainer("minio/minio:RELEASE.2025-09-07T16-13-09Z") as container:
        yield container


@pytest.fixture(scope="session")
def minio_client(minio_container: MinioContainer) -> Minio:
    return minio_container.get_client()


@pytest.fixture(scope="session")
def redis_container() -> Generator[RedisContainer]:
    with RedisContainer("redis:alpine3.22") as container:
        yield container


@pytest.fixture(scope="session")
def redis_url(redis_container: RedisContainer) -> str:
    host: str = redis_container.get_container_host_ip()
    port: int = redis_container.get_exposed_port(6379)
    return f"redis://{host}:{port}"


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
async def analysis_data(seed_stocks: list[Stock]) -> list[Analysis]:
    analysis: list[Analysis] = [
        Analysis(
            stock_id=seed_stocks[0].id,
            metrics={"pe_ratio": 15.5, "pb_ratio": 2.3},
            score=85.5,
            filtered=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Analysis(
            stock_id=seed_stocks[1].id,
            metrics={"pe_ratio": 12.3, "pb_ratio": 1.8},
            score=78.0,
            filtered=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
        Analysis(
            stock_id=seed_stocks[2].id,
            metrics={"pe_ratio": 20.1, "pb_ratio": 3.2},
            score=72.5,
            filtered=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        ),
    ]
    return analysis


@pytest_asyncio.fixture
async def app_factory(
    async_session: AsyncSession,
    redis_url: str,
) -> Callable[[list[APIRouter]], FastAPI]:
    def make_app(routers: list[APIRouter]) -> FastAPI:
        app = FastAPI()
        for r in routers:
            app.include_router(r)

        async def override_get_db() -> AsyncGenerator[AsyncSession]:
            yield async_session

        async def override_get_redis() -> AsyncGenerator[Redis]:
            redis: Redis = Redis.from_url(redis_url)
            yield redis
            redis.flushall()

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_redis] = override_get_redis
        return app

    return make_app


@pytest_asyncio.fixture
async def client_factory() -> Callable[[FastAPI], Awaitable[AsyncClient]]:
    async def make_client(app: FastAPI) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

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
        sign_flag:
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
def cninfo_adapter(
    yaml_config_dir: Path, async_limiter: AsyncLimiter, wait_strategy: wait_exponential
) -> CNInfoAdapter:
    return CNInfoAdapter(
        config_dir=yaml_config_dir,
        timeout=2.0,
        limiter=async_limiter,
        retry_attempts=2,
        wait=wait_strategy,
    )


@pytest.fixture
def cninfo_data() -> dict[str, Any]:
    data: dict[str, Any] = {}
    data_dir: Path = Path(__file__).parents[2] / "data" / "api" / "cninfo"
    for file in data_dir.iterdir():
        with file.open("r", encoding="utf-8") as f:
            content: dict[str, Any] = json.load(f)
            content = content["data"]
            data[file.name.removesuffix(".json")] = content
    return data


@pytest.fixture
def yfinance_data() -> dict[str, Any]:
    data: dict[str, Any] = {}
    data_dir: Path = Path(__file__).parents[2] / "data" / "api" / "yahoo"
    for file in data_dir.iterdir():
        with file.open("r", encoding="utf-8") as f:
            content: dict[str, Any] = json.load(f)
            data[file.name.removesuffix(".json")] = {"records": content}
    return data


@pytest.fixture
def stock_data(
    cninfo_data: dict[str, Any],
    yfinance_data: dict[str, Any],
) -> dict[str, Any]:
    return {**cninfo_data, **yfinance_data}


@pytest.fixture
def rule_adapter(stock_data: dict[str, Any]) -> RuleAdapter:
    rule_file_path: Path = (
        Path(__file__).parents[2] / "configs" / "rules" / "scoring_rules_sample.yaml"
    )
    adapter = RuleAdapter(rule_file_path=rule_file_path)
    adapter.set_data(stock_data)
    return adapter


@pytest_asyncio.fixture
async def mcp_client(
    app_factory: Callable[[list[APIRouter]], FastAPI],
) -> AsyncGenerator[Client[FastMCPTransport]]:
    app: FastAPI = app_factory([analysis_router, stock_router])
    mcp: FastMCPOpenAPI = FastMCP.from_fastapi(app=app)
    async with Client(mcp) as client:
        yield client

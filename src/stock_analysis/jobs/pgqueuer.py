"""Build and configure PgQueuer for stock analysis jobs."""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from pgqueuer import PgQueuer
from psycopg import AsyncConnection

from stock_analysis.adapters.cninfo import CNInfoAdapter
from stock_analysis.adapters.rule import RuleAdapter
from stock_analysis.adapters.yahoo import YahooFinanceAdapter
from stock_analysis.jobs.analyzer import analyze
from stock_analysis.jobs.crawler import crawl
from stock_analysis.logger import get_logger
from stock_analysis.schemas.api import JobPayload
from stock_analysis.services.database import async_session
from stock_analysis.services.stock import StockService
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    import logging

    from pgqueuer.models import Context, Job, Schedule
    from pgqueuer.queries import Queries
    from pgqueuer.types import JobId
    from psycopg.rows import TupleRow

    from stock_analysis.services.stock import Stock
    from stock_analysis.settings import Settings


async def get_connection() -> AsyncConnection[TupleRow]:
    """Get the database connection.

    Returns:
        AsyncConnection[TupleRow]: The database connection.
    """
    settings: Settings = get_settings()
    return await AsyncConnection.connect(
        dbname=settings.database_db,
        user=settings.database_user,
        password=settings.database_password.get_secret_value(),
        host=settings.database_host,
        port=settings.database_port,
        autocommit=True,
    )


async def create_pgqueuer_with_connection(
    connection: AsyncConnection[TupleRow],
) -> PgQueuer:
    """Build and configure a PgQueuer with an existing database connection.

    Creates a PgQueuer instance for async job processing and registers
    job handlers for crawling and analyzing stock data.

    Args:
        connection: Active AsyncConnection to PostgreSQL database.

    Returns:
        Configured PgQueuer instance ready for job queueing and processing.
    """
    resources: dict[str, Any] = {
        "cninfo_adapter": CNInfoAdapter(get_settings().config_dir),
        "yahoo_finance_adapter": YahooFinanceAdapter(),
        "rule_adapter": RuleAdapter(get_settings().rule_file_path),
        "logger": get_logger("pgqueuer", "worker"),
    }
    pgq: PgQueuer = PgQueuer.from_psycopg_connection(connection, resources=resources)

    @pgq.entrypoint("crawl_stock_data", accepts_context=True)
    async def crawl_stock_data(job: Job, ctx: Context) -> None:
        cninfo_adapter: CNInfoAdapter = ctx.resources["cninfo_adapter"]
        yahoo_finance_adapter: YahooFinanceAdapter = ctx.resources[
            "yahoo_finance_adapter"
        ]
        logger: logging.Logger = ctx.resources["logger"]
        await crawl(job, cninfo_adapter, yahoo_finance_adapter, logger)

    @pgq.entrypoint("analyze_stock_data", accepts_context=True)
    async def analyze_stock_data(job: Job, ctx: Context) -> None:
        rule_adapter: RuleAdapter = ctx.resources["rule_adapter"]
        logger: logging.Logger = ctx.resources["logger"]
        await analyze(job, rule_adapter, logger)

    @pgq.entrypoint("update_stock_data", accepts_context=True)
    async def update_stock_data(_job: Job, ctx: Context) -> None:
        queries: Queries = pgq.qm.queries
        logger: logging.Logger = ctx.resources["logger"]
        payloads: list[bytes | None] = []
        async with async_session() as db:
            stock_service = StockService(db)
            stocks: list[Stock] = await stock_service.get_stocks()
            for stock in stocks:
                payload: JobPayload = JobPayload(stock_code=stock.stock_code)
                payloads.append(payload.model_dump_json().encode())
        job_ids: list[JobId] = await queries.enqueue(
            ["crawl_stock_data"] * len(stocks),
            payloads,
            priority=[0] * len(stocks),
            execute_after=[timedelta(minutes=i) for i in range(len(stocks))],
        )
        logger.info("Enqueued crawl jobs: %s", repr(job_ids))

    @pgq.entrypoint("analyze_all_stock_data", accepts_context=True)
    async def analyze_all_stock_data(_job: Job, ctx: Context) -> None:
        queries: Queries = pgq.qm.queries
        logger: logging.Logger = ctx.resources["logger"]
        payloads: list[bytes | None] = []
        async with async_session() as db:
            stock_service = StockService(db)
            stocks: list[Stock] = await stock_service.get_stocks()
            for stock in stocks:
                payload: JobPayload = JobPayload(stock_code=stock.stock_code)
                payloads.append(payload.model_dump_json().encode())
        job_ids: list[JobId] = await queries.enqueue(
            ["analyze_stock_data"] * len(stocks),
            payloads,
            priority=[0] * len(stocks),
        )
        logger.info("Enqueued analyze jobs: %s", repr(job_ids))

    @pgq.schedule("update_all_stocks", "0 0 1 1,7 *")
    async def update_all_stocks(schedule: Schedule) -> None:
        logger: logging.Logger = pgq.resources["logger"]
        logger.info(
            "Starting schedule %s at %s",
            repr(schedule),
            repr(datetime.now().astimezone()),
        )
        queries: Queries = pgq.qm.queries
        await queries.enqueue("update_stock_data", None, priority=10)

    @pgq.schedule("analyze_all_stocks", "0 0 1 2,8 *")
    async def analyze_all_stocks(schedule: Schedule) -> None:
        logger: logging.Logger = pgq.resources["logger"]
        logger.info(
            "Starting schedule %s at %s",
            repr(schedule),
            repr(datetime.now().astimezone()),
        )
        queries: Queries = pgq.qm.queries
        await queries.enqueue("analyze_all_stock_data", None, priority=10)

    return pgq


async def create_pgqueuer() -> PgQueuer:
    """Build and configure a PgQueuer with a new database connection.

    Creates a new database connection and initializes a PgQueuer instance
    with job handlers.

    Returns:
        Configured PgQueuer instance ready for job processing.
    """
    connection: AsyncConnection = await get_connection()
    return await create_pgqueuer_with_connection(connection)


async def close_connection(conn: AsyncConnection) -> None:
    """Close the database connection.

    Args:
        conn: The AsyncConnection to close.
    """
    await conn.close()

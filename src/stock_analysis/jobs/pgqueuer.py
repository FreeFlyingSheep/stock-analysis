"""Build and configure PgQueuer for stock analysis jobs."""

from typing import TYPE_CHECKING, Any

from pgqueuer import PgQueuer
from psycopg import AsyncConnection

from stock_analysis.adaptors.cninfo import CNInfoAdaptor
from stock_analysis.adaptors.rule import RuleAdaptor
from stock_analysis.adaptors.yahoo import YahooFinanceAdaptor
from stock_analysis.jobs.analyzer import analyze
from stock_analysis.jobs.crawler import crawl
from stock_analysis.logger import get_logger
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    import logging

    from pgqueuer import Job
    from pgqueuer.models import Context

    from stock_analysis.settings import Settings


async def get_connection() -> AsyncConnection:
    """Get the database connection.

    Returns:
        AsyncConnection: The database connection.
    """
    settings: Settings = get_settings()
    return await AsyncConnection.connect(
        dbname=settings.database_db,
        user=settings.database_user,
        password=settings.database_password,
        host=settings.database_host,
        port=settings.database_port,
        autocommit=True,
    )


async def create_pgqueuer_with_connection(connection: AsyncConnection) -> PgQueuer:
    """Build and configure a PgQueuer using an existing connection.

    Args:
        connection (AsyncConnection): The database connection to use.

    Returns:
        PgQueuer: Configured PgQueuer instance.
    """
    resources: dict[str, Any] = {
        "cninfo_adaptor": CNInfoAdaptor(),
        "yahoo_finance_adaptor": YahooFinanceAdaptor(),
        "rule_adaptor": RuleAdaptor(get_settings().rule_file_path),
        "logger": get_logger("pgqueuer"),
    }
    pgq: PgQueuer = PgQueuer.from_psycopg_connection(connection, resources=resources)

    @pgq.entrypoint("crawl_stock_data")
    async def crawl_stock_data(job: Job) -> None:
        ctx: Context = pgq.qm.get_context(job.id)
        cninfo_adaptor: CNInfoAdaptor = ctx.resources["cninfo_adaptor"]
        yahoo_finance_adaptor: YahooFinanceAdaptor = ctx.resources[
            "yahoo_finance_adaptor"
        ]
        logger: logging.Logger = ctx.resources["logger"]
        await crawl(job, cninfo_adaptor, yahoo_finance_adaptor, logger)

    @pgq.entrypoint("analyze_stock_data")
    async def analyze_stock_data(job: Job) -> None:
        ctx: Context = pgq.qm.get_context(job.id)
        rule_adaptor: RuleAdaptor = ctx.resources["rule_adaptor"]
        logger: logging.Logger = ctx.resources["logger"]
        await analyze(job, rule_adaptor, logger)

    return pgq


async def create_pgqueuer() -> PgQueuer:
    """Build and configure a PgQueuer.

    Returns:
        PgQueuer: Configured PgQueuer instance.
    """
    connection: AsyncConnection = await get_connection()
    return await create_pgqueuer_with_connection(connection)


async def close_connection(conn: AsyncConnection) -> None:
    """Close the database connection."""
    await conn.close()

"""Analyze stock data by enqueueing analyze jobs."""

import asyncio
import logging
from typing import TYPE_CHECKING

from stock_analysis.jobs.pgqueuer import create_pgqueuer_with_connection, get_connection
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from pgqueuer import PgQueuer
    from pgqueuer.queries import Queries
    from psycopg import AsyncConnection
    from psycopg.rows import TupleRow

    from stock_analysis.settings import Settings

logger: logging.Logger = logging.getLogger(__name__)


async def main() -> None:
    """Update stock data by enqueueing update jobs."""
    settings: Settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    logger.info("Enqueuing update_stock_data job...")

    conn: AsyncConnection[TupleRow] = await get_connection()
    pgq: PgQueuer = create_pgqueuer_with_connection(conn)

    queries: Queries = pgq.qm.queries
    await queries.enqueue("analyze_all_stocks", None, priority=10)

    await asyncio.sleep(5)
    await conn.close()
    logger.info("Finished.")


if __name__ == "__main__":
    asyncio.run(main())

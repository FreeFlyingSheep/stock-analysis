"""Drop the database if it exists."""

import logging
from typing import TYPE_CHECKING

import psycopg
from psycopg import sql

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from stock_analysis.settings import Settings

logger: logging.Logger = logging.getLogger(__name__)


def drop_database(settings: Settings) -> None:
    """Drop the database if it exists.

    Args:
        settings: Application settings containing database connection details.

    Raises:
        ValueError: If database name is missing or invalid.
    """
    with (
        psycopg.connect(
            dbname="postgres",
            user=settings.database_user,
            password=settings.database_password,
            host=settings.database_host,
            port=settings.database_port,
            autocommit=True,
        ) as conn,
        conn.cursor() as cur,
    ):
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (settings.database_db,)
        )
        exists: bool = cur.fetchone() is not None
        if exists:
            cur.execute(
                sql.SQL("DROP DATABASE {}").format(sql.Identifier(settings.database_db))
            )
            logger.info("Dropped database: %s", settings.database_db)
        else:
            logger.info("Database does not exist: %s", settings.database_db)


def main() -> None:
    """Drop the database.

    Entry point for the database drop script. Initializes settings
    and logging, then drops the database if it exists.
    """
    settings: Settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    drop_database(settings)


if __name__ == "__main__":
    main()

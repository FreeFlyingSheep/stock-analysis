"""Create the database if it does not exist."""

import logging
from typing import TYPE_CHECKING

import psycopg
from psycopg import sql

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from stock_analysis.settings import Settings

logger: logging.Logger = logging.getLogger(__name__)


def create_database(settings: Settings) -> None:
    """Create the database if it does not exist. Enable the pgvector extension.

    Args:
        settings: Application settings containing database connection details.
    """
    with (
        psycopg.connect(
            dbname="postgres",
            user=settings.database_user,
            password=settings.database_password.get_secret_value(),
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
        if not exists:
            cur.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(settings.database_db)
                )
            )
            cur.execute(sql.SQL("CREATE EXTENSION vector"))
            logger.info("Created database: %s", settings.database_db)
        else:
            logger.info("Database already exists: %s", settings.database_db)


def main() -> None:
    """Create the database.

    Entry point for the database creation script. Initializes settings
    and logging, then creates the database if it doesn't exist.
    """
    settings: Settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    create_database(settings)


if __name__ == "__main__":
    main()

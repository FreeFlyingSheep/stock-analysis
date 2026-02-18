"""Create the Langfuse database and bucket if it does not exist."""

import logging
import os
from typing import TYPE_CHECKING

import psycopg
from minio import Minio
from psycopg import sql

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from stock_analysis.settings import Settings

logger: logging.Logger = logging.getLogger(__name__)


def getenv_required(name: str) -> str:
    """Get an environment variable or raise an error if it's not set.

    Args:
        name: The name of the environment variable to retrieve.

    Returns:
        The value of the environment variable.

    Raises:
        RuntimeError: If the environment variable is not set.
    """
    v: str | None = os.getenv(name)
    if v is None:
        msg = f"Missing required env var: {name}"
        raise RuntimeError(msg)
    return v


def create_database(settings: Settings) -> None:
    """Create the database if it does not exist.

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
        langfuse_user: str = getenv_required("LANGFUSE_DB_USER")
        langfuse_pass: str = getenv_required("LANGFUSE_DB_PASSWORD")
        langfuse_db: str = getenv_required("LANGFUSE_DB_NAME")

        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (langfuse_user,))
        if cur.fetchone() is None:
            cur.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                    sql.Identifier(langfuse_user),
                    sql.Literal(langfuse_pass),
                )
            )
            logger.info("Created role: %s", langfuse_user)
        else:
            logger.info("Role already exists: %s", langfuse_user)

        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (langfuse_db,))
        if cur.fetchone() is None:
            cur.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(langfuse_db),
                    sql.Identifier(langfuse_user),
                )
            )
            logger.info("Created database: %s (owner=%s)", langfuse_db, langfuse_user)
        else:
            logger.info("Database already exists: %s", langfuse_db)

        cur.execute(
            sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
                sql.Identifier(langfuse_db),
                sql.Identifier(langfuse_user),
            )
        )
        logger.info("Granted privileges on %s to %s", langfuse_db, langfuse_user)


def create_bucket(settings: Settings) -> None:
    """Create the S3 bucket if it does not exist.

    Args:
        settings: Application settings containing S3 connection details.
    """
    client = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_user,
        secret_key=settings.minio_password.get_secret_value(),
        secure=settings.minio_secure,
    )

    bucket_name: str = getenv_required("LANGFUSE_S3_BUCKET")
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        logger.info("Created S3 bucket: %s", bucket_name)
    else:
        logger.info("S3 bucket already exists: %s", bucket_name)


def main() -> None:
    """Create the database and S3 bucket if they do not exist.

    Entry point for the database creation script. Initializes settings
    and logging, then creates the database if it doesn't exist.
    """
    settings: Settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    create_database(settings)
    create_bucket(settings)


if __name__ == "__main__":
    main()

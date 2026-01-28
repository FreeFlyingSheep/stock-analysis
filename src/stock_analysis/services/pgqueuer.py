"""PgQueuer worker for stock analysis jobs."""

from asyncio import Lock
from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi import (
    HTTPException,
    Request,  # noqa: TC002
)
from pgqueuer import PgQueuer

from stock_analysis.jobs.pgqueuer import get_connection

if TYPE_CHECKING:
    from fastapi import FastAPI
    from psycopg import AsyncConnection
    from psycopg.rows import TupleRow


_pgq_lock = Lock()


async def create_pgqueuer_with_connection(
    connection: AsyncConnection[TupleRow],
) -> PgQueuer:
    """Build and configure a PgQueuer with an existing database connection.

    Args:
        connection: Active AsyncConnection to PostgreSQL database.

    Returns:
        Configured PgQueuer instance ready for job queueing and processing.
    """
    return PgQueuer.from_psycopg_connection(connection)


async def get_pgqueuer(request: Request) -> PgQueuer:
    """Get PgQueuer connection. Initializes if not already present.

    Args:
        request: FastAPI request object for accessing app state.

    Returns:
        PgQueuer worker connection.

    Raises:
        HTTPException: If the PgQueuer connection cannot be established.
    """
    if getattr(request.app.state, "pgq", None) is not None:
        return request.app.state.pgq

    async with _pgq_lock:
        if getattr(request.app.state, "pgq", None) is not None:
            return request.app.state.pgq

        try:
            conn: AsyncConnection = await get_connection()
            request.app.state.conn = conn
        except Exception as e:
            request.app.state.conn = None
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="Database unavailable",
            ) from e

        try:
            pgq: PgQueuer = await create_pgqueuer_with_connection(conn)
            request.app.state.pgq = pgq
        except Exception as e:
            request.app.state.pgq = None
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="Job queue unavailable",
            ) from e
        else:
            return pgq


async def close_pgqueuer(app: FastAPI) -> None:
    """Close the database connection.

    Args:
        app: FastAPI application instance.
    """
    if getattr(app.state, "conn", None) is not None:
        await app.state.conn.close()

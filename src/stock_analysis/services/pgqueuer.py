"""PgQueuer worker for stock analysis jobs."""

from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi import (
    HTTPException,
    Request,  # noqa: TC002
)
from pgqueuer import PgQueuer

if TYPE_CHECKING:
    from psycopg_pool import AsyncConnectionPool


async def get_pgqueuer(request: Request) -> PgQueuer:
    """Get PgQueuer connection.

    Args:
        request: FastAPI request object for accessing app state.

    Returns:
        PgQueuer worker connection.

    Raises:
        HTTPException: If the PgQueuer connection cannot be established.
    """
    pool: AsyncConnectionPool | None = getattr(request.app.state, "pgq_pool", None)
    if pool is None:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="Job queue unavailable",
        )

    async with pool.connection() as conn:
        return PgQueuer.from_psycopg_connection(conn)

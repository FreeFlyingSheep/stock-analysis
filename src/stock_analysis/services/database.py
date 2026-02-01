"""Database service providing async session management and engine setup."""

from collections.abc import AsyncGenerator  # noqa: TC003
from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi import (
    HTTPException,
    Request,  # noqa: TC002
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,  # noqa: TC002
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import (
        async_sessionmaker,
    )


async def get_db(request: Request) -> AsyncGenerator[AsyncSession]:
    """Get a database session.

    Args:
        request: FastAPI request object for accessing app state.

    Returns:
        Async generator yielding a database session.

    Raises:
        HTTPException: If database session is not initialized.
    """
    db_session: async_sessionmaker[AsyncSession] | None = getattr(
        request.app.state, "db_session", None
    )
    if not db_session:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="Database session not initialized.",
        )

    async with db_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

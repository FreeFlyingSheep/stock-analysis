"""Database service providing async session management and engine setup."""

from collections.abc import AsyncGenerator  # noqa: TC003
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncSession,  # noqa: TC002
    async_sessionmaker,
    create_async_engine,
)

from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
    )

    from stock_analysis.settings import Settings

settings: Settings = get_settings()
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Get a database session from the session maker.

    Provides an async context manager for database sessions. The session is
    automatically committed when exiting successfully and rolled back if an
    exception occurs.

    Yields:
        AsyncSession instance for database operations.

    Raises:
        Exception: Propagates any exception that occurs during session usage.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

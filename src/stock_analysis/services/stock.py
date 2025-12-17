"""Stock service for managing stock operations."""

from typing import TYPE_CHECKING

from sqlalchemy import func, select

from stock_analysis.models.stock import Stock

if TYPE_CHECKING:
    from sqlalchemy import Result, Select
    from sqlalchemy.ext.asyncio import AsyncSession


class StockService:
    """Service for managing stock operations.

    This service provides methods for querying and managing stock data,
    including filtering, pagination, and aggregation operations.

    Attributes:
        db: AsyncSession instance for database operations.
    """

    db: AsyncSession
    """Database session."""

    def __init__(self, db_session: AsyncSession) -> None:
        """Initialize the StockService with a database session.

        Args:
            db_session: AsyncSession instance for database operations.
        """
        self.db: AsyncSession = db_session

    async def get_stocks(
        self,
        classification: str | None = None,
        industry: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Stock]:
        """Get stocks with optional filtering.

        Args:
            classification: Optional filter by classification category.
            industry: Optional filter by industry sector.
            limit: Maximum number of results to return. If None, returns all.
            offset: Number of results to skip for pagination. Defaults to 0.

        Returns:
            list[Stock]: List of Stock objects matching the criteria.
        """
        query: Select[tuple[Stock]] = select(Stock)

        if classification:
            query = query.where(Stock.classification == classification)
        if industry:
            query = query.where(Stock.industry == industry)

        query = query.order_by(Stock.stock_code)

        if offset > 0:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        result: Result[tuple[Stock]] = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_stock_by_code(self, stock_code: str) -> Stock | None:
        """Get a single stock by its code.

        Args:
            stock_code: The unique stock code to search for.

        Returns:
            Stock | None: Stock object if found, None otherwise.
        """
        result: Result[tuple[Stock]] = await self.db.execute(
            select(Stock).where(Stock.stock_code == stock_code)
        )
        return result.scalar_one_or_none()

    async def get_classifications(self) -> list[str]:
        """Get all unique classifications from stocks.

        Returns:
            list[str]: Sorted list of unique classification names.
        """
        result: Result[tuple[str]] = await self.db.execute(
            select(Stock.classification).distinct().order_by(Stock.classification)
        )
        return list(result.scalars().all())

    async def get_industries(self) -> list[str]:
        """Get all unique industries from stocks.

        Returns:
            list[str]: Sorted list of unique industry names.
        """
        result: Result[tuple[str]] = await self.db.execute(
            select(Stock.industry).distinct().order_by(Stock.industry)
        )
        return list(result.scalars().all())

    async def count_stocks(
        self,
        classification: str | None = None,
        industry: str | None = None,
    ) -> int:
        """Count stocks matching the given criteria.

        Args:
            classification: Optional filter by classification category.
            industry: Optional filter by industry sector.

        Returns:
            int: Total number of stocks matching the criteria.
        """
        query: Select[tuple[int]] = select(func.count(Stock.stock_code))

        if classification:
            query = query.where(Stock.classification == classification)
        if industry:
            query = query.where(Stock.industry == industry)

        result: Result[tuple[int]] = await self.db.execute(query)
        return result.scalar() or 0

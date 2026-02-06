"""Stock managing service."""

from typing import TYPE_CHECKING

from sqlalchemy import func, select

from stock_analysis.models.analysis import Analysis
from stock_analysis.models.cninfo import CNInfoAPIResponse
from stock_analysis.models.stock import Stock
from stock_analysis.models.yahoo import YahooFinanceAPIResponse

if TYPE_CHECKING:
    from sqlalchemy import Result, Select
    from sqlalchemy.ext.asyncio import AsyncSession


class StockService:
    """Service for database operations on stock and related data."""

    db: AsyncSession
    """Database session for all operations."""

    def __init__(self, db_session: AsyncSession) -> None:
        """Initialize the StockService with a database session.

        Args:
            db_session: AsyncSession instance for database operations.
        """
        self.db: AsyncSession = db_session

    async def get_stocks(
        self,
        search: str | None = None,
        classification: str | None = None,
        industry: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Stock]:
        """Get stocks with optional filtering.

        Args:
            search: Optional search string to filter stocks by code or name.
            classification: Optional filter by classification category.
            industry: Optional filter by industry sector.
            limit: Maximum number of results to return. If None, returns all.
            offset: Number of results to skip for pagination. Defaults to 0.

        Returns:
            List of Stock objects matching the criteria.
        """
        query: Select[tuple[Stock]] = select(Stock)

        if search:
            search_pattern: str = f"%{search}%"
            query = query.where(
                (Stock.stock_code.ilike(search_pattern))
                | (Stock.company_name.ilike(search_pattern))
            )

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
            Stock object if found, None otherwise.
        """
        result: Result[tuple[Stock]] = await self.db.execute(
            select(Stock).where(Stock.stock_code == stock_code)
        )
        return result.scalar_one_or_none()

    async def get_classifications(self) -> list[str]:
        """Get all unique classifications from stocks.

        Returns:
            Sorted list of unique classification names.
        """
        result: Result[tuple[str]] = await self.db.execute(
            select(Stock.classification).distinct().order_by(Stock.classification)
        )
        return list(result.scalars().all())

    async def get_industries(self, classification: str | None = None) -> list[str]:
        """Get all unique industries from stocks.

        Args:
            classification: Optional filter by classification category.

        Returns:
            Sorted list of unique industry names.
        """
        query: Select[tuple[str]] = (
            select(Stock.industry).distinct().order_by(Stock.industry)
        )

        if classification:
            query = query.where(Stock.classification == classification)

        result: Result[tuple[str]] = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_stocks(
        self,
        search: str | None = None,
        classification: str | None = None,
        industry: str | None = None,
    ) -> int:
        """Count stocks matching the given criteria.

        Args:
            search: Optional search string to filter stocks by code or name.
            classification: Optional filter by classification category.
            industry: Optional filter by industry sector.

        Returns:
            Total number of stocks matching the criteria.
        """
        query: Select[tuple[int]] = select(func.count(Stock.id))

        if search:
            search_pattern: str = f"%{search}%"
            query = query.where(
                (Stock.stock_code.ilike(search_pattern))
                | (Stock.company_name.ilike(search_pattern))
            )

        if classification:
            query = query.where(Stock.classification == classification)
        if industry:
            query = query.where(Stock.industry == industry)

        result: Result[tuple[int]] = await self.db.execute(query)
        return result.scalar() or 0

    async def get_cninfo_api_responses_by_stock_id(
        self, stock_id: int
    ) -> list[CNInfoAPIResponse]:
        """Get CNInfo API responses for a given stock ID.

        Args:
            stock_id: The ID of the stock to retrieve API responses for.

        Returns:
            List of CNInfoAPIResponse objects associated with the stock.
        """
        result: Result[tuple[CNInfoAPIResponse]] = await self.db.execute(
            select(CNInfoAPIResponse).where(CNInfoAPIResponse.stock_id == stock_id)
        )
        return list(result.scalars().all())

    async def get_yahoo_finance_api_responses_by_stock_id(
        self, stock_id: int
    ) -> list[YahooFinanceAPIResponse]:
        """Get Yahoo Finance API responses for a given stock ID.

        Args:
            stock_id: The ID of the stock to retrieve API responses for.

        Returns:
            List of YahooFinanceAPIResponse objects associated with the stock.
        """
        result: Result[tuple[YahooFinanceAPIResponse]] = await self.db.execute(
            select(YahooFinanceAPIResponse).where(
                YahooFinanceAPIResponse.stock_id == stock_id
            )
        )
        return list(result.scalars().all())

    async def get_analysis(
        self, limit: int | None = None, offset: int = 0
    ) -> list[Analysis]:
        """Get all analysis records.

        Args:
            limit: Maximum number of results to return. If None, returns all.
            offset: Number of results to skip for pagination. Defaults to 0.

        Returns:
            List of Analysis objects.
        """
        query: Select[tuple[Analysis]] = select(Analysis)

        if offset > 0:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        result: Result[tuple[Analysis]] = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_analysis_by_stock_id(self, stock_id: int) -> list[Analysis]:
        """Get analysis records for a given stock ID.

        Args:
            stock_id: The ID of the stock to retrieve analysis records for.

        Returns:
            List of Analysis objects associated with the stock.
        """
        result: Result[tuple[Analysis]] = await self.db.execute(
            select(Analysis).where(Analysis.stock_id == stock_id)
        )
        return list(result.scalars().all())

    async def count_analysis(self) -> int:
        """Count total analysis records.

        Returns:
            Total number of analysis records.
        """
        result: Result[tuple[int]] = await self.db.execute(
            select(func.count(Analysis.id))
        )
        return result.scalar() or 0

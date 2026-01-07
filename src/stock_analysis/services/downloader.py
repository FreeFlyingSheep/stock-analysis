"""Data downloader service."""

from typing import TYPE_CHECKING

from pydantic import ValidationError

from stock_analysis.models.cninfo import CNInfoAPIResponse
from stock_analysis.models.yahoo import YahooFinanceAPIResponse
from stock_analysis.schemas.api import CNInfoAPIResponseIn, YahooFinanceAPIResponseIn

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from stock_analysis.adaptors.cninfo import CNInfoAdaptor
    from stock_analysis.adaptors.yahoo import YahooFinanceAdaptor
    from stock_analysis.schemas.api import CNInfoFetchResult


class DownloaderError(RuntimeError):
    """Raised when a download operation fails."""


class CNInfoDownloader:
    """Service for downloading raw CNInfo API data."""

    _session: AsyncSession
    _adaptor: CNInfoAdaptor

    def __init__(
        self,
        session: AsyncSession,
        adaptor: CNInfoAdaptor,
    ) -> None:
        """Initialize the downloader.

        Args:
            session: Database session for storing raw data.
            adaptor: CNInfo API adaptor for fetching data.
        """
        self._session = session
        self._adaptor = adaptor

    async def download(
        self,
        endpoint: str,
        stock_id: int,
        **kwargs: str,
    ) -> int:
        """Download data from a CNInfo endpoint and store raw response.

        Fetches data from the specified CNInfo endpoint with given parameters
        and stores the raw response along with metadata in the database.

        Args:
            endpoint: CNInfo endpoint name (e.g., 'balance_sheets', 'income_statement').
            stock_id: ID of the stock for which data is being downloaded.
            **kwargs: Additional query parameters for the API request.

        Returns:
            The ID of the created CNInfoAPIResponse record.

        Raises:
            DownloaderError: If the download or storage validation fails.
        """
        try:
            async with self._adaptor:
                result: CNInfoFetchResult = await self._adaptor.fetch(
                    endpoint, **kwargs
                )
            try:
                raw_record = CNInfoAPIResponseIn(
                    endpoint=endpoint,
                    stock_id=stock_id,
                    params=result.request_params,
                    response_code=result.response_code,
                    raw_json=result.raw_json,
                )
            except ValidationError as e:
                msg: str = f"Validation error for {endpoint}"
                raise DownloaderError(msg) from e
            else:
                record = CNInfoAPIResponse(**raw_record.model_dump())
                self._session.add(record)
                await self._session.flush()
                return record.id
        except Exception as e:
            msg = f"Error downloading {endpoint}"
            raise DownloaderError(msg) from e


class YahooFinanceDownloader:
    """Service for downloading raw Yahoo Finance API data."""

    _session: AsyncSession
    _adaptor: YahooFinanceAdaptor

    def __init__(
        self,
        session: AsyncSession,
        adaptor: YahooFinanceAdaptor,
    ) -> None:
        """Initialize the downloader.

        Args:
            session: Database session for storing raw data.
            adaptor: Yahoo Finance API adaptor for fetching data.
        """
        self._session = session
        self._adaptor = adaptor

    async def download(
        self,
        stock_id: int,
        symbol: str,
    ) -> int:
        """Download historical stock data from Yahoo Finance and store response.

        Fetches historical price and volume data for the given stock symbol
        and stores the raw JSON response along with metadata in the database.

        Args:
            stock_id: ID of the stock for which data is being downloaded.
            symbol: Stock ticker symbol (e.g., '600000.SH').

        Returns:
            The ID of the created YahooFinanceAPIResponse record.

        Raises:
            DownloaderError: If the download or storage validation fails.
        """
        raw_json: str = await self._adaptor.get_stock_history(symbol)
        try:
            raw_record = YahooFinanceAPIResponseIn(
                stock_id=stock_id,
                params={
                    "symbol": symbol,
                    "period": self._adaptor.period,
                    "interval": self._adaptor.interval,
                },
                raw_json=raw_json,
            )
        except ValidationError as e:
            msg: str = f"Validation error for Yahoo Finance API with symbol {symbol}"
            raise DownloaderError(msg) from e
        else:
            record = YahooFinanceAPIResponse(**raw_record.model_dump())
            self._session.add(record)
            await self._session.flush()
            return record.id

"""Data downloader service."""

from typing import TYPE_CHECKING

from pydantic import ValidationError

from stock_analysis.models.api import CNInfoAPIResponse
from stock_analysis.schemas.api import CNInfoAPIResponseIn

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from stock_analysis.adaptors.cninfo import CNInfoAdaptor
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

        Args:
            endpoint: CNInfo endpoint name (e.g., 'balance_sheets').
            stock_id: ID of the stock for which data is being downloaded.
            **kwargs: Additional parameters for the request.

        Returns:
            The ID of the created record.

        Raises:
            DownloaderError: If the download or storage fails.
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

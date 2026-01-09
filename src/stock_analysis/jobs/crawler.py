"""Job to crawl stock data."""

from datetime import datetime
from typing import TYPE_CHECKING

from dateutil.relativedelta import relativedelta
from pydantic import ValidationError

from stock_analysis.adaptors.cninfo import CNInfoAdaptor
from stock_analysis.adaptors.stock import get_stock_code_with_market
from stock_analysis.schemas.api import JobPayload
from stock_analysis.services.database import async_session
from stock_analysis.services.downloader import CNInfoDownloader, YahooFinanceDownloader
from stock_analysis.services.stock import StockService

if TYPE_CHECKING:
    import logging

    from pgqueuer.models import Job
    from sqlalchemy.ext.asyncio import AsyncSession

    from stock_analysis.adaptors.cninfo import CNInfoAdaptor
    from stock_analysis.adaptors.yahoo import YahooFinanceAdaptor
    from stock_analysis.models.cninfo import CNInfoAPIResponse
    from stock_analysis.models.yahoo import YahooFinanceAPIResponse
    from stock_analysis.services.stock import Stock


class CrawlerError(RuntimeError):
    """Error raised during stock data crawling operations."""


async def _crawl_cninfo_stock_data(
    db: AsyncSession,
    payload: JobPayload,
    adaptor: CNInfoAdaptor,
    logger: logging.Logger,
) -> None:
    """Crawl and store stock data from all CNInfo API endpoints.

    Downloads data from all available CNInfo endpoints for the specified stock
    and stores raw responses in the database.

    Args:
        db: Database session for storing responses.
        payload: Job payload containing stock code.
        adaptor: CNInfo adaptor for fetching endpoint data.
        logger: Logger for recording operations.

    Raises:
        CrawlerError: If stock not found or download fails.
    """
    stock_service = StockService(db)
    stock: Stock | None = await stock_service.get_stock_by_code(payload.stock_code)
    if not stock:
        msg: str = f"Stock with code {payload.stock_code} not found."
        raise CrawlerError(msg)

    responses: list[
        CNInfoAPIResponse
    ] = await stock_service.get_cninfo_api_responses_by_stock_id(stock.id)
    if responses:
        need_update: bool = False
        for r in responses:
            if r.updated_at >= datetime.now().astimezone() - relativedelta(months=6):
                need_update = True
                break

        if not need_update:
            logger.info(
                "Data for stock %s already exists. Skipping download.",
                payload.stock_code,
            )
            return

    logger.info("Starting download for stock %s", payload.stock_code)

    try:
        downloader: CNInfoDownloader = CNInfoDownloader(db, adaptor)
        record_ids: list[int] = [
            await downloader.download(endpoint, stock.id, stock_code=payload.stock_code)
            for endpoint in adaptor.available_endpoints
        ]
        await db.commit()
        logger.info(
            "Successfully downloaded data for stock %s: record IDs %s",
            payload.stock_code,
            record_ids,
        )
    except Exception as e:
        await db.rollback()
        msg = f"Failed to download stock data for stock {payload.stock_code}."
        logger.exception(msg, exc_info=e)
        raise CrawlerError(msg) from e


async def crawl_yahoo_finance_stock_data(
    db: AsyncSession,
    payload: JobPayload,
    adaptor: YahooFinanceAdaptor,
    logger: logging.Logger,
) -> None:
    """Crawl and store stock data from Yahoo Finance API.

    Downloads historical stock price and volume data from Yahoo Finance
    and stores the raw JSON response in the database.

    Args:
        db: Database session for storing responses.
        payload: Job payload containing stock code.
        adaptor: Yahoo Finance adaptor for fetching historical data.
        logger: Logger for recording operations.

    Raises:
        CrawlerError: If stock not found or download fails.
    """
    stock_service = StockService(db)
    stock: Stock | None = await stock_service.get_stock_by_code(payload.stock_code)
    if not stock:
        msg: str = f"Stock with code {payload.stock_code} not found."
        raise CrawlerError(msg)

    responses: list[
        YahooFinanceAPIResponse
    ] = await stock_service.get_yahoo_finance_api_responses_by_stock_id(stock.id)
    if responses:
        logger.info(
            "Yahoo Finance data for stock %s already exists. Skipping download.",
            payload.stock_code,
        )
        return

    logger.info("Starting Yahoo Finance download for stock %s", payload.stock_code)

    symbol: str = get_stock_code_with_market(payload.stock_code)
    try:
        downloader = YahooFinanceDownloader(db, adaptor)
        record_id: int = await downloader.download(
            stock_id=stock.id,
            symbol=symbol,
        )
        await db.commit()
        logger.info(
            "Successfully downloaded Yahoo Finance data for stock %s: record ID %d",
            payload.stock_code,
            record_id,
        )
    except Exception as e:
        await db.rollback()
        msg = f"Failed to download Yahoo Finance data for stock {symbol}."
        raise CrawlerError(msg) from e


async def crawl(
    job: Job,
    cninfo_adaptor: CNInfoAdaptor,
    yahoo_finance_adaptor: YahooFinanceAdaptor,
    logger: logging.Logger,
) -> None:
    """Crawl stock data from both CNInfo and Yahoo Finance sources.

    Main job entrypoint that orchestrates data crawling from both CNInfo
    and Yahoo Finance endpoints for a single stock.

    Args:
        job: Job instance containing encoded payload.
        cninfo_adaptor: CNInfo adaptor for endpoint data.
        yahoo_finance_adaptor: Yahoo Finance adaptor for historical data.
        logger: Logger for recording operations.

    Raises:
        CrawlerError: If job payload is missing or invalid JSON.
    """
    if not job.payload:
        msg: str = "Job payload is missing."
        raise CrawlerError(msg)
    try:
        payload_str: str = job.payload.decode()
        logger.info("Job payload: %s", payload_str)
        payload: JobPayload = JobPayload.model_validate_json(payload_str)
    except ValidationError as e:
        msg = f"Invalid job payload: {e.errors()}"
        raise CrawlerError(msg) from e

    async with async_session() as db:
        await _crawl_cninfo_stock_data(
            db,
            payload,
            cninfo_adaptor,
            logger,
        )
        await crawl_yahoo_finance_stock_data(
            db,
            payload,
            yahoo_finance_adaptor,
            logger,
        )

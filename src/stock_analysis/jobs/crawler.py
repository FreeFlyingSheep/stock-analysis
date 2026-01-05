"""Job to crawl stock data from CNInfo."""

from typing import TYPE_CHECKING

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

    from stock_analysis.adaptors.cninfo import CNInfoAdaptor
    from stock_analysis.adaptors.yahoo import YahooFinanceAdaptor
    from stock_analysis.models.yahoo import YahooFinanceAPIResponse
    from stock_analysis.services.stock import AsyncSession, CNInfoAPIResponse, Stock


class CrawlerError(RuntimeError):
    """Custom error for crawler issues."""


async def _crawl_cninfo_stock_data(
    db: AsyncSession,
    payload: JobPayload,
    adaptor: CNInfoAdaptor,
    logger: logging.Logger,
) -> None:
    """Crawl stock data from CNInfo.

    Args:
        db: The database session.
        payload: The job payload containing stock code.
        adaptor: The CNInfo adaptor for API interactions.
        logger: Logger for logging messages.

    Raises:
        CrawlerError: If the stock is not found or download fails.
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
    """Crawl stock data from Yahoo Finance.

    Args:
        db: The database session.
        payload: The job payload containing stock code.
        adaptor: The Yahoo Finance adaptor for API interactions.
        logger: Logger for logging messages.

    Returns:
        The ID of the created record.

    Raises:
        CrawlerError: If the download or storage fails.
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
    """Crawl stock data.

    Args:
        job: The job instance containing payload and metadata.
        cninfo_adaptor: The CNInfo adaptor for API interactions.
        yahoo_finance_adaptor: The Yahoo Finance adaptor for API interactions.
        logger: Logger for logging messages.

    Raises:
        CrawlerError: If the job payload is missing or invalid.
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
        await _crawl_cninfo_stock_data(db, payload, cninfo_adaptor, logger)
        await crawl_yahoo_finance_stock_data(
            db,
            payload,
            yahoo_finance_adaptor,
            logger,
        )

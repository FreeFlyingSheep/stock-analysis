"""Job to crawl stock data from CNInfo."""

from typing import TYPE_CHECKING

from pydantic import ValidationError

from stock_analysis.adaptors.cninfo import CNInfoAdaptor
from stock_analysis.schemas.api import CNInfoJobPayload
from stock_analysis.services.database import async_session
from stock_analysis.services.downloader import CNInfoDownloader
from stock_analysis.services.stock import StockService

if TYPE_CHECKING:
    import logging

    from pgqueuer.models import Job

    from stock_analysis.adaptors.cninfo import CNInfoAdaptor
    from stock_analysis.services.stock import AsyncSession, CNInfoAPIResponse, Stock


class CrawlerError(RuntimeError):
    """Custom error for crawler issues."""


async def _crawl_cninfo_stock_data(
    db: AsyncSession,
    payload: CNInfoJobPayload,
    adaptor: CNInfoAdaptor,
    logger: logging.Logger,
) -> None:
    """Crawl stock data from CNInfo.

    Args:
        db (AsyncSession): The database session.
        payload (CNInfoJobPayload): The job payload containing stock code.
        adaptor (CNInfoAdaptor): The CNInfo adaptor for API interactions.
        logger (logging.Logger): Logger for logging messages.

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


async def crawl(job: Job, adaptor: CNInfoAdaptor, logger: logging.Logger) -> None:
    """Crawl stock data.

    Args:
        job (Job): The job instance containing payload and metadata.
        adaptor (CNInfoAdaptor): The CNInfo adaptor for API interactions.
        logger (logging.Logger): Logger for logging messages.

    Raises:
        CrawlerError: If the job payload is missing or invalid.
    """
    if not job.payload:
        msg: str = "Job payload is missing."
        raise CrawlerError(msg)
    try:
        logger.info("Job payload: %s", job.payload.decode())
        payload: CNInfoJobPayload = CNInfoJobPayload.model_validate_json(
            job.payload.decode()
        )
    except ValidationError as e:
        msg = f"Invalid job payload: {e.errors()}"
        raise CrawlerError(msg) from e

    async with async_session() as db:
        await _crawl_cninfo_stock_data(db, payload, adaptor, logger)

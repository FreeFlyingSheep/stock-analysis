"""Job to analyze stock data using scoring rules."""

from typing import TYPE_CHECKING

from pydantic import ValidationError

from stock_analysis.schemas.api import JobPayload
from stock_analysis.services.analyzer import Analyzer
from stock_analysis.services.database import async_session
from stock_analysis.services.stock import StockService

if TYPE_CHECKING:
    import logging

    from pgqueuer.models import Job
    from sqlalchemy.ext.asyncio import AsyncSession

    from stock_analysis.adaptors.rule import RuleAdaptor
    from stock_analysis.models.analysis import Analysis
    from stock_analysis.services.stock import Stock


class AnalyzerError(Exception):
    """Error raised during stock analysis job processing."""


async def _analyze_stock_data(
    db: AsyncSession,
    payload: JobPayload,
    adaptor: RuleAdaptor,
    logger: logging.Logger,
) -> None:
    """Analyze stock data using scoring rules.

    Applies scoring rules to compute metrics and scores for a single stock,
    and stores the analysis results in the database.

    Args:
        db: Database session for reading/writing analysis.
        payload: Job payload containing stock code.
        adaptor: Rule adaptor for applying scoring rules.
        logger: Logger for recording operations.

    Raises:
        AnalyzerError: If stock not found or analysis fails.
    """
    stock_service = StockService(db)
    stock: Stock | None = await stock_service.get_stock_by_code(payload.stock_code)
    if not stock:
        msg: str = f"Stock with code {payload.stock_code} not found."
        raise AnalyzerError(msg)

    analysis: list[Analysis] = await stock_service.get_analysis_by_stock_id(stock.id)
    if analysis:
        logger.info(
            "Analysis for stock %s already exists. Skipping analysis.",
            payload.stock_code,
        )
        return

    logger.info("Analyzing stock data for stock code: %s", payload.stock_code)

    try:
        analyzer = Analyzer(db, adaptor)
        record_ids: list[int] = await analyzer.analyze(stock.id)
        await db.commit()
        logger.info(
            "Analysis completed for stock code: %s, record IDs: %d",
            payload.stock_code,
            record_ids,
        )
    except Exception as e:
        await db.rollback()
        msg = f"Failed to analyze stock data for stock {payload.stock_code}."
        logger.exception(msg, exc_info=e)
        raise AnalyzerError(msg) from e


async def analyze(
    job: Job,
    rule_adaptor: RuleAdaptor,
    logger: logging.Logger,
) -> None:
    """Analyze stock data from job payload.

    Main job entrypoint that orchestrates stock analysis using configured
    scoring rules.

    Args:
        job: Job instance containing encoded payload.
        rule_adaptor: Rule adaptor for computing scores and metrics.
        logger: Logger for recording operations.

    Raises:
        AnalyzerError: If job payload is missing or invalid JSON.
    """
    if not job.payload:
        msg: str = "Job payload is missing."
        raise AnalyzerError(msg)
    try:
        payload_str: str = job.payload.decode()
        logger.info("Job payload: %s", payload_str)
        payload: JobPayload = JobPayload.model_validate_json(payload_str)
    except ValidationError as e:
        msg = f"Invalid job payload: {e.errors()}"
        raise AnalyzerError(msg) from e

    async with async_session() as db:
        await _analyze_stock_data(
            db,
            payload,
            rule_adaptor,
            logger,
        )

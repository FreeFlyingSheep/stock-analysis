"""Stock data analyzer service."""

from typing import TYPE_CHECKING

from pydantic import ValidationError

from stock_analysis.models.analysis import Analysis
from stock_analysis.schemas.analysis import AnalysisIn

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from stock_analysis.adapters.rule import RuleAdapter


class AnalyzerError(RuntimeError):
    """Error raised when stock analysis fails."""


class Analyzer:
    """Service for analyzing stock data using scoring rules.

    Applies scoring rules and metrics to compute analysis scores and
    determines if stocks meet filter criteria.

    Attributes:
        _session: AsyncSession for database operations.
        _adapter: RuleAdapter for applying scoring rules.
    """

    _session: AsyncSession
    _adapter: RuleAdapter

    def __init__(self, session: AsyncSession, adapter: RuleAdapter) -> None:
        """Initialize the analyzer.

        Args:
            session: Database session for reading/writing data.
            adapter: Rule adapter for applying analysis rules.
        """
        self._session = session
        self._adapter = adapter

    async def analyze(self, stock_id: int) -> list[int]:
        """Analyze a stock and compute metrics and scores.

        Applies scoring rules to compute financial metrics, generates an overall
        score, and applies filter criteria.

        Args:
            stock_id: ID of the stock to analyze.

        Returns:
            List of created Analysis record IDs.

        Raises:
            AnalyzerError: If analysis data validation fails.
        """
        metrics: dict[str, float] = self._adapter.metrics()
        score: float = self._adapter.score()
        filtered: bool = self._adapter.apply_filter()
        try:
            analysis_in: AnalysisIn = AnalysisIn(
                stock_id=stock_id,
                metrics=metrics,
                score=score,
                filtered=filtered,
            )
        except ValidationError as e:
            msg: str = f"Failed to validate analysis data for stock {stock_id}: {e}"
            raise AnalyzerError(msg) from e
        else:
            analysis: Analysis = Analysis(**analysis_in.model_dump())
            self._session.add(analysis)
            await self._session.flush()
            return [analysis.id]

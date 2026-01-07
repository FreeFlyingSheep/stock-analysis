"""Stock data analyzer service."""

from typing import TYPE_CHECKING

from pydantic import ValidationError

from stock_analysis.models.analysis import Analysis
from stock_analysis.schemas.analysis import AnalysisIn

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from stock_analysis.adaptors.rule import RuleAdaptor


class AnalyzerError(RuntimeError):
    """Raised when analyzing fails."""


class Analyzer:
    """Service for analyzing raw stock data into normalized tables."""

    _session: AsyncSession
    _adaptor: RuleAdaptor

    def __init__(self, session: AsyncSession, adaptor: RuleAdaptor) -> None:
        """Initialize the analyzer.

        Args:
            session: Database session for reading/writing data.
            adaptor: Rule adaptor for applying analysis rules.
        """
        self._session = session
        self._adaptor = adaptor

    async def analyze(self, stock_id: int) -> list[int]:
        """Analyze a stock.

        Args:
            stock_id: ID of the stock to analyze.

        Raises:
            AnalyzerError: If analyzing fails.
        """
        metrics: dict[str, float] = self._adaptor.metrics()
        score: float = self._adaptor.score()
        filtered: bool = self._adaptor.apply_filter()
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

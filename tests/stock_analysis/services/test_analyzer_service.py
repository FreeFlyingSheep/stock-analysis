from typing import TYPE_CHECKING

import pytest

from stock_analysis.models.analysis import Analysis
from stock_analysis.services.analyzer import Analyzer

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from stock_analysis.adapters.rule import RuleAdapter
    from stock_analysis.models.stock import Stock


@pytest.mark.asyncio
async def test_analyzer(
    async_session: AsyncSession, seed_stocks: list[Stock], rule_adapter: RuleAdapter
) -> None:
    stock_id: int = seed_stocks[0].id

    analyzer = Analyzer(async_session, rule_adapter)
    await analyzer.analyze(stock_id)
    result: Analysis | None = await async_session.get(Analysis, stock_id)
    assert result is not None
    assert result.metrics != {}
    assert result.score != 0.0
    assert result.filtered is False

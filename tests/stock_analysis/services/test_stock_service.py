from typing import TYPE_CHECKING

import pytest

from stock_analysis.services.stock import StockService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from stock_analysis.models.stock import Stock


@pytest.mark.asyncio
async def test_get_stocks_filters(
    async_session: AsyncSession,
    seed_stocks: list[Stock],
) -> None:
    service = StockService(async_session)
    finance: str = "金融业"

    finance_stocks: list[Stock] = await service.get_stocks(classification=finance)
    expected_stocks: list[Stock] = [
        stock for stock in seed_stocks if stock.classification == finance
    ]
    expected_stocks.sort(key=lambda s: s.stock_code)
    assert len(finance_stocks) == len(expected_stocks)
    for i, stock in enumerate(expected_stocks):
        assert stock.stock_code == finance_stocks[i].stock_code


@pytest.mark.asyncio
async def test_get_stocks_pagination(
    async_session: AsyncSession, seed_stocks: list[Stock]
) -> None:
    service = StockService(async_session)
    limit: int = 1
    offset: int = 2

    paged_stocks: list[Stock] = await service.get_stocks(limit=limit, offset=offset)
    expected_stocks: list[Stock] = seed_stocks[offset : offset + limit]
    assert len(paged_stocks) == len(expected_stocks)
    for i, stock in enumerate(expected_stocks):
        assert stock.stock_code == paged_stocks[i].stock_code


@pytest.mark.asyncio
async def test_get_stock_by_code(
    async_session: AsyncSession, seed_stocks: list[Stock]
) -> None:
    service = StockService(async_session)
    expected_stock: Stock = seed_stocks[1]
    missing_stock_code: str = "999999"

    found: Stock | None = await service.get_stock_by_code(expected_stock.stock_code)
    assert found is not None
    assert found.company_name == expected_stock.company_name

    missing: Stock | None = await service.get_stock_by_code(missing_stock_code)
    assert missing is None


@pytest.mark.asyncio
async def test_get_classifications_and_industries(
    async_session: AsyncSession, seed_stocks: list[Stock]
) -> None:
    service = StockService(async_session)
    classifications: list[str] = await service.get_classifications()
    industries: list[str] = await service.get_industries()

    assert set(classifications) == {stock.classification for stock in seed_stocks}
    assert set(industries) == {stock.industry for stock in seed_stocks}


@pytest.mark.asyncio
async def test_count_stocks_with_filters(
    async_session: AsyncSession, seed_stocks: list[Stock]
) -> None:
    service = StockService(async_session)
    technology: str = "科技"
    banking: str = "银行业"

    total: int = await service.count_stocks()
    assert total == len(seed_stocks)

    tech_count: int = await service.count_stocks(classification=technology)
    assert tech_count == sum(1 for s in seed_stocks if s.classification == technology)

    banking_count: int = await service.count_stocks(industry=banking)
    assert banking_count == sum(1 for s in seed_stocks if s.industry == banking)

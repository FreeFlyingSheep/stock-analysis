import logging
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest

from stock_analysis.jobs.crawler import CrawlerError, _crawl_cninfo_stock_data
from stock_analysis.models.cninfo import CNInfoAPIResponse
from stock_analysis.models.stock import Stock
from stock_analysis.schemas.api import JobPayload

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from stock_analysis.adaptors.cninfo import CNInfoAdaptor


@pytest.fixture
def logger() -> logging.Logger:
    return logging.getLogger("crawler-test")


@pytest.mark.asyncio
async def test_stock_not_found(
    async_session: AsyncSession, cninfo_adaptor: CNInfoAdaptor, logger: logging.Logger
) -> None:
    payload: JobPayload = JobPayload(stock_code="999999")
    with pytest.raises(CrawlerError, match="not found"):
        await _crawl_cninfo_stock_data(async_session, payload, cninfo_adaptor, logger)


@pytest.mark.asyncio
async def test_skip(
    async_session: AsyncSession,
    cninfo_adaptor: CNInfoAdaptor,
    logger: logging.Logger,
    caplog: pytest.LogCaptureFixture,
) -> None:
    stock: Stock = Stock(
        stock_code="000001",
        company_name="测试公司",
        classification="测试业",
        industry="测试行业",
    )
    async_session.add(stock)
    await async_session.flush()

    response: CNInfoAPIResponse = CNInfoAPIResponse(
        stock_id=stock.id,
        endpoint="test_endpoint",
        params={"stock_code": "000001"},
        response_code=HTTPStatus.OK,
        raw_json={"data": "test"},
    )
    async_session.add(response)
    await async_session.flush()

    payload: JobPayload = JobPayload(stock_code="000001")
    with caplog.at_level("INFO"):
        await _crawl_cninfo_stock_data(async_session, payload, cninfo_adaptor, logger)
        assert "Skipping download." in caplog.text

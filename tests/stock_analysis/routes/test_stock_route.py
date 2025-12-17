from collections.abc import AsyncGenerator  # noqa: TC003
from http import HTTPStatus
from inspect import signature
from math import ceil
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

from stock_analysis.routers.stock import get_stocks, router
from stock_analysis.schemas.stock import StockApiResponse

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from inspect import Signature

    from fastapi import APIRouter, FastAPI
    from httpx import AsyncClient, Response

    from stock_analysis.models.stock import Stock
    from stock_analysis.schemas.stock import StockPage


@pytest_asyncio.fixture
async def client(
    app_factory: Callable[[list[APIRouter]], FastAPI],
    client_factory: Callable[[FastAPI], Awaitable[AsyncClient]],
) -> AsyncGenerator[AsyncClient]:
    app: FastAPI = app_factory([router])
    client: AsyncClient = await client_factory(app)
    yield client
    await client.aclose()


@pytest.mark.anyio
async def test_get_stocks_default(
    client: AsyncClient,
    seed_stocks: list[Stock],
) -> None:
    resp: Response = await client.get("/stocks")
    assert resp.status_code == HTTPStatus.OK

    payload: StockApiResponse = StockApiResponse.model_validate(resp.json())
    assert set(payload.data.classifications) == {
        stock.classification for stock in seed_stocks
    }
    assert set(payload.data.industries) == {stock.industry for stock in seed_stocks}

    page: StockPage = payload.data.stock_page
    sig: Signature = signature(get_stocks)
    expected_size: int = sig.parameters["size"].default
    expected_page: int = sig.parameters["page"].default
    assert page.page_num == expected_page
    assert page.page_size == expected_size
    assert page.total == ceil(len(seed_stocks) / expected_size)
    assert len(page.data) == len(seed_stocks)


@pytest.mark.anyio
async def test_get_stocks_filter_by_classification(
    client: AsyncClient, seed_stocks: list[Stock]
) -> None:
    finance: str = "金融业"
    resp: Response = await client.get("/stocks", params={"classification": finance})
    assert resp.status_code == HTTPStatus.OK

    payload: StockApiResponse = StockApiResponse.model_validate(resp.json())
    page: StockPage = payload.data.stock_page
    expected_stocks: list[Stock] = [
        stock for stock in seed_stocks if stock.classification == finance
    ]
    expected_stocks.sort(key=lambda s: s.stock_code)
    assert len(page.data) == len(expected_stocks)
    for i, stock in enumerate(expected_stocks):
        assert stock.stock_code == page.data[i].stock_code


@pytest.mark.anyio
async def test_get_stocks_filter_by_industry(
    client: AsyncClient, seed_stocks: list[Stock]
) -> None:
    software: str = "软件"
    resp: Response = await client.get("/stocks", params={"industry": software})
    assert resp.status_code == HTTPStatus.OK

    payload: StockApiResponse = StockApiResponse.model_validate(resp.json())
    page: StockPage = payload.data.stock_page
    expected_stocks: list[Stock] = [
        stock for stock in seed_stocks if stock.industry == software
    ]
    expected_stocks.sort(key=lambda s: s.stock_code)
    assert len(page.data) == len(expected_stocks)
    for i, stock in enumerate(expected_stocks):
        assert stock.stock_code == page.data[i].stock_code


@pytest.mark.anyio
async def test_get_stocks_page_validation(client: AsyncClient) -> None:
    resp: Response = await client.get("/stocks", params={"page": 0})
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

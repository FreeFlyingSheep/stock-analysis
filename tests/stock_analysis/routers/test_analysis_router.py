from http import HTTPStatus
from inspect import signature
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from stock_analysis.routers.analysis import get_analysis, router
from stock_analysis.schemas.analysis import AnalysisApiResponse

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Awaitable, Callable
    from inspect import Signature

    from fastapi import APIRouter, FastAPI
    from httpx import AsyncClient, Response

    from stock_analysis.models.analysis import Analysis
    from stock_analysis.models.stock import Stock


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
async def test_get_analysis_default(client: AsyncClient) -> None:
    resp: Response = await client.get("/analysis")
    assert resp.status_code == HTTPStatus.OK

    payload: AnalysisApiResponse = AnalysisApiResponse.model_validate(resp.json())
    sig: Signature = signature(get_analysis)
    expected_page_num: int = sig.parameters["page"].default
    expected_page_size: int = sig.parameters["size"].default
    assert payload.data.page_num == expected_page_num
    assert payload.data.page_size == expected_page_size


@pytest.mark.anyio
async def test_get_analysis_custom_page_size(client: AsyncClient) -> None:
    expected_page_size = 10
    resp: Response = await client.get("/analysis", params={"size": expected_page_size})
    assert resp.status_code == HTTPStatus.OK
    payload: AnalysisApiResponse = AnalysisApiResponse.model_validate(resp.json())
    assert payload.data.page_size == expected_page_size


@pytest.mark.anyio
async def test_get_analysis_pagination(client: AsyncClient) -> None:
    expected_page_num = 2
    expected_page_size = 25
    resp: Response = await client.get(
        "/analysis",
        params={"page": expected_page_num, "size": expected_page_size},
    )
    assert resp.status_code == HTTPStatus.OK
    payload: AnalysisApiResponse = AnalysisApiResponse.model_validate(resp.json())
    assert payload.data.page_num == expected_page_num
    assert payload.data.page_size == expected_page_size


@pytest.mark.anyio
async def test_get_analysis_invalid_page(client: AsyncClient) -> None:
    resp: Response = await client.get("/analysis", params={"page": 0})
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_get_analysis_invalid_size(client: AsyncClient) -> None:
    resp: Response = await client.get("/analysis", params={"size": 0})
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_get_analysis_size_exceeds_max(client: AsyncClient) -> None:
    resp: Response = await client.get("/analysis", params={"size": 201})
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_get_analysis_details_not_found(client: AsyncClient) -> None:
    resp: Response = await client.get("/analysis/999999")
    assert resp.status_code == HTTPStatus.NOT_FOUND
    assert "not found" in resp.json()["detail"].lower()


@pytest.mark.anyio
async def test_get_analysis_details(
    client: AsyncClient,
    seed_stocks: list[Stock],
    analysis_data: list[Analysis],
    async_session: AsyncSession,
) -> None:
    async_session.add_all(analysis_data)
    await async_session.flush()

    stock_code: str = seed_stocks[0].stock_code
    resp: Response = await client.get(f"/analysis/{stock_code}")
    assert resp.status_code == HTTPStatus.OK
    assert "data" in resp.json()

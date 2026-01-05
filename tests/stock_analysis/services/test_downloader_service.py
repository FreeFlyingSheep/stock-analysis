from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

from stock_analysis.models.cninfo import CNInfoAPIResponse
from stock_analysis.services.downloader import CNInfoDownloader

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Awaitable, Callable

    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

    from stock_analysis.adaptors.cninfo import CNInfoAdaptor
    from stock_analysis.models.stock import Stock


@pytest_asyncio.fixture
async def client_ok(
    httpx_client_factory: Callable[
        [int, bytes], Awaitable[tuple[AsyncClient, dict[str, int]]]
    ],
) -> AsyncGenerator[tuple[AsyncClient, dict[str, int]]]:
    result: tuple[AsyncClient, dict[str, int]] = await httpx_client_factory(
        HTTPStatus.OK, b'{"code": 200, "records": []}'
    )
    client: AsyncClient = result[0]
    yield client, result[1]
    await client.aclose()


@pytest_asyncio.fixture
async def cninfo_adaptor_ok(
    cninfo_adaptor: CNInfoAdaptor, client_ok: tuple[AsyncClient, dict[str, int]]
) -> AsyncGenerator[CNInfoAdaptor]:
    cninfo_adaptor.client = client_ok[0]
    yield cninfo_adaptor
    await cninfo_adaptor.client.aclose()


@pytest.mark.asyncio
async def test_download_success(
    async_session: AsyncSession,
    seed_stocks: list[Stock],
    cninfo_adaptor_ok: CNInfoAdaptor,
) -> None:
    """Test successful download and storage of API response."""
    endpoint = "income_statement"
    stock_id: int = seed_stocks[0].id
    stock_code: str = seed_stocks[0].stock_code

    downloader = CNInfoDownloader(async_session, cninfo_adaptor_ok)
    record_id: int = await downloader.download(
        endpoint, stock_id=stock_id, stock_code=stock_code
    )
    result: CNInfoAPIResponse | None = await async_session.get(
        CNInfoAPIResponse, record_id
    )
    assert result is not None
    assert result.endpoint == endpoint
    assert result.params == {"scode": stock_code, "sign": 1}
    assert result.response_code == HTTPStatus.OK
    assert result.raw_json == {"code": HTTPStatus.OK, "records": []}

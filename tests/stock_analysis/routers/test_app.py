from collections.abc import AsyncGenerator  # noqa: TC003
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

from stock_analysis.routers.app import app, message

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from fastapi import FastAPI
    from httpx import AsyncClient, Response


@pytest_asyncio.fixture
async def client(
    client_factory: Callable[[FastAPI], Awaitable[AsyncClient]],
) -> AsyncGenerator[AsyncClient]:
    client: AsyncClient = await client_factory(app)
    yield client
    await client.aclose()


@pytest.mark.anyio
async def test_root(client: AsyncClient) -> None:
    resp: Response = await client.get("/")
    assert resp.status_code == HTTPStatus.OK

    payload: dict = resp.json()
    assert payload == {"message": message}

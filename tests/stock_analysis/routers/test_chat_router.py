from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

from stock_analysis.routers.chat import router
from stock_analysis.schemas.chat import ChatThreadsResponse

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Awaitable, Callable

    from fastapi import APIRouter, FastAPI
    from httpx import AsyncClient, Response

    from stock_analysis.models.chat import ChatThread


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
async def test_get_chats_with_threads(
    client: AsyncClient,
    seed_chat_threads: list[ChatThread],
) -> None:
    resp: Response = await client.get("/chats")
    assert resp.status_code == HTTPStatus.OK

    payload: ChatThreadsResponse = ChatThreadsResponse.model_validate(resp.json())
    assert len(payload.data) == sum(
        1 for thread in seed_chat_threads if thread.status == "active"
    )
    for thread in payload.data:
        assert thread.status == "active"
        assert thread.thread_id is not None
        assert thread.title is not None

"""Chat router definitions."""

from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi import (
    APIRouter,
    HTTPException,
    Request,  # noqa: TC002
)
from fastapi.responses import StreamingResponse

from stock_analysis.schemas.chat import ChatMessageIn  # noqa: TC001
from stock_analysis.services.mcp import get_mcp

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from stock_analysis.agent.graph import ChatAgent

router = APIRouter()


@router.post("/chat")
async def chat(request: Request, chat_message: ChatMessageIn) -> StreamingResponse:
    """Send a message to the chat agent and stream responses.

    Args:
        request: Chat message request containing user message.
        chat_message: Chat message input schema.

    Returns:
        StreamingResponse with SSE events.

    Raises:
        HTTPException: If the chat operation fails.
    """
    agent: ChatAgent = await get_mcp(request)

    async def event_generator() -> AsyncGenerator[str]:
        """Generate SSE events from agent stream."""
        try:
            async for content in agent.astream_events(chat_message.message):
                yield f"event: token\ndata: {content}\n\n"
            yield "event: done\n\n"
        except Exception as e:
            msg: str = "Error during chat streaming"
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg
            ) from e

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )

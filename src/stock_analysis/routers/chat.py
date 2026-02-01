"""Chat router definitions."""

from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.responses import StreamingResponse
from langchain_mcp_adapters.client import MultiServerMCPClient  # noqa: TC002

from stock_analysis.agent.graph import ChatAgent
from stock_analysis.schemas.chat import ChatMessageIn  # noqa: TC001
from stock_analysis.services.mcp import get_mcp

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from langchain_core.tools.base import BaseTool


router = APIRouter()


@router.post("/chat")
async def chat(
    chat_message: ChatMessageIn,
    client: Annotated[MultiServerMCPClient, Depends(get_mcp)],
) -> StreamingResponse:
    """Send a message to the chat agent and stream responses.

    Args:
        chat_message: Chat message input schema.
        client: MCP client dependency.

    Returns:
        StreamingResponse with SSE events.

    Raises:
        HTTPException: If the chat operation fails.
    """
    tools: list[BaseTool] = await client.get_tools()
    agent = ChatAgent(tools)

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

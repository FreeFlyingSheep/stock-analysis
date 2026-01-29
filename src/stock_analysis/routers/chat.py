"""Chat router definitions."""

from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi import (
    APIRouter,
    HTTPException,
    Request,  # noqa: TC002
)
from langchain.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from stock_analysis.schemas.chat import (
    ChatMessageIn,  # noqa: TC001
    ChatMessageOut,
    ChatResponseOut,
)
from stock_analysis.services.mcp import get_mcp

if TYPE_CHECKING:
    from langchain_core.messages import AnyMessage

    from stock_analysis.agent.graph import ChatAgent

router = APIRouter()


def _convert_messages(messages: list[AnyMessage]) -> list[ChatMessageOut]:
    """Convert langchain messages to chat message output schema.

    Args:
        messages: List of langchain messages.

    Returns:
        List of chat message output schemas.
    """
    result: list[ChatMessageOut] = []
    for message in messages:
        if isinstance(message, SystemMessage):
            content: str = message.text
            result.append(ChatMessageOut(role="system", content=content))
        elif isinstance(message, HumanMessage):
            content = message.text
            result.append(ChatMessageOut(role="user", content=content))
        elif isinstance(message, AIMessage):
            content = message.text
            result.append(ChatMessageOut(role="assistant", content=content))
        elif isinstance(message, ToolMessage):
            content = message.text
            result.append(ChatMessageOut(role="tool", content=content))
        else:
            msg: str = f"Unsupported message type: {type(message)}"
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=msg)
    return result


@router.post("/chat")
async def chat(request: Request, chat_message: ChatMessageIn) -> ChatResponseOut:
    """Send a message to the chat agent and get a response.

    Args:
        request: Chat message request containing user message.
        chat_message: Chat message input schema.

    Returns:
        Chat response with assistant message and conversation history.

    Raises:
        HTTPException: If the chat operation fails.
    """
    agent: ChatAgent = await get_mcp(request)

    result: dict = await agent.ainvoke(chat_message.message)

    messages: list[AnyMessage] = result.get("messages", [])
    if not isinstance(messages[-1], AIMessage):
        msg: str = "No response from agent"
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=msg)

    return ChatResponseOut(
        messages=_convert_messages(messages),
    )

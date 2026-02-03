"""Chat schemas for stock analysis application."""

from typing import Literal

from stock_analysis.schemas.base import BaseSchema


class ChatStartIn(BaseSchema):
    """Input schema for starting a chat thread.

    Attributes:
        thread_id: ID of the chat thread.
        message_id: ID of the initial message.
        message: Message content.
        stock_code: Optional stock code related to the chat.
    """

    thread_id: str
    message_id: str
    message: str
    stock_code: str | None = None


class ChatStartOut(BaseSchema):
    """Output schema for starting a chat thread.

    Attributes:
        stream_url: URL for streaming chat responses.
    """

    stream_url: str


class StreamEvent(BaseSchema):
    """Schema for streaming chat events.

    Attributes:
        id: Event sequence identifier.
        event: Type of event.
        data: Event data content.
    """

    id: str
    event: Literal["token", "done", "error", "ping"]
    data: str

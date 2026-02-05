"""Chat schemas for stock analysis application."""

from datetime import datetime
from typing import Literal

from stock_analysis.schemas.base import BaseSchema


class ChatThreadIn(BaseSchema):
    """Schema representing a chat thread.

    Attributes:
        thread_id: Unique identifier for the chat thread.
        title: Title of the chat thread.
        status: Current status of the chat thread (active or deleted).
    """

    thread_id: str
    title: str
    status: Literal["active", "deleted"]


class ChatThreadCreateIn(BaseSchema):
    """Schema for creating a chat thread.

    Attributes:
        thread_id: Optional client-provided thread identifier.
        title: Optional title for the chat thread.
        status: Optional status for the chat thread.
    """

    thread_id: str | None = None
    title: str | None = None
    status: Literal["active", "deleted"] = "active"


class ChatThreadUpdateIn(BaseSchema):
    """Schema for updating a chat thread.

    Attributes:
        title: Optional title for the chat thread.
        status: Optional status for the chat thread.
    """

    title: str | None = None
    status: Literal["active", "deleted"] | None = None


class ChatThreadOut(ChatThreadIn):
    """Output schema for chat thread.

    Extends ChatThreadIn with timestamp fields.

    Attributes:
        created_at: Timestamp when the thread was created.
        updated_at: Timestamp when the thread was last updated.
    """

    created_at: datetime
    updated_at: datetime


class ChatStartIn(BaseSchema):
    """Input schema for starting a chat thread.

    Attributes:
        thread_id: ID of the chat thread.
        message_id: ID of the initial message.
        message: Message content.
        locale: Locale for the chat interaction.
        stock_code: Optional stock code related to the chat.
    """

    thread_id: str
    message_id: str
    message: str
    locale: str
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


class ChatThreadsResponse(BaseSchema):
    """Schema for chat threads response.

    Attributes:
        data: List of chat thread IDs.
    """

    data: list[ChatThreadOut]


class ChatMessageOut(BaseSchema):
    """Schema for chat message output.

    Attributes:
        role: Role of the message sender (human or ai).
        content: Content of the chat message.
    """

    role: Literal["human", "ai"]
    content: str


class ChatThreadDetailResponse(BaseSchema):
    """Schema for chat thread details.

    Attributes:
        data: List of messages in the chat thread.
    """

    data: list[ChatMessageOut]

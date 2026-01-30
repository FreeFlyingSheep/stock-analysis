"""Chat schemas for stock analysis application."""

from typing import Literal

from stock_analysis.schemas.base import BaseSchema


class ChatMessageIn(BaseSchema):
    """Input schema for chat messages.

    Attributes:
        message: The user's message content.
    """

    message: str


class StreamEvent(BaseSchema):
    """Generic stream event schema.

    Attributes:
        type: Type of the event.
        data: Content of the event, if applicable.
    """

    event: Literal["token", "done"]
    data: str | None = None

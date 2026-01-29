"""Chat schemas for stock analysis application."""

from typing import Literal

from stock_analysis.schemas.base import BaseSchema


class ChatMessageIn(BaseSchema):
    """Input schema for chat messages.

    Attributes:
        message: The user's message content.
    """

    message: str


class ChatMessageOut(BaseSchema):
    """Output schema for chat messages.

    Attributes:
        role: The role of the message sender.
        content: The message content.
    """

    role: Literal["system", "user", "assistant", "tool"]
    content: str


class ChatResponseOut(BaseSchema):
    """Output schema for chat responses.

    Attributes:
        messages: Response messages.
    """

    messages: list[ChatMessageOut]

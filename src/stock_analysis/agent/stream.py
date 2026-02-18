"""Helpers for processing chat streaming events."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from langchain_core.messages.ai import AIMessageChunk
    from langchain_core.runnables.schema import StreamEvent


async def astream_chat_response(event: StreamEvent) -> AsyncGenerator[str]:
    """Process a stream event and yield the content of AI message chunks.

    Args:
        event: A stream event containing information about the chat response.

    Yields:
        The content of AI message chunks as they are received.
    """
    kind: str = event.get("event", "")
    raw_metadata: object = event.get("metadata")
    metadata: dict = raw_metadata if isinstance(raw_metadata, dict) else {}
    node_name: str | None = metadata.get("langgraph_node")

    if kind == "on_chat_model_stream" and node_name == "generate_answer":
        chunk: AIMessageChunk | None = event.get("data", {}).get("chunk")
        if chunk and chunk.content:
            content: str | list[str | dict] = chunk.content
            if isinstance(content, str):
                yield content
            else:
                text_parts: list[str] = [
                    p if isinstance(p, str) else str(p) for p in content
                ]
                text: str = "".join(text_parts)
                yield text

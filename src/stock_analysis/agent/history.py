"""Helpers for building chat history transcripts from graph snapshots."""

from typing import TYPE_CHECKING

from langchain.messages import AIMessage, HumanMessage
from opentelemetry import trace

if TYPE_CHECKING:
    from langgraph.pregel.debug import StateSnapshot


tracer: trace.Tracer = trace.get_tracer(__name__)


async def build_chat_history(snaps: list[StateSnapshot]) -> list[dict[str, str]]:
    """Build a chat transcript from a list of graph state snapshots.

    Args:
        snaps: A list of graph state snapshots, ordered from oldest to newest.

    Returns:
        A list of message dicts representing the chat history.
    """
    seen_ids: set[str] = set()
    transcript: list[dict[str, str]] = []

    for snap in snaps:
        for m in snap.values.get("messages", []):
            if not isinstance(m, (HumanMessage, AIMessage)):
                continue

            mid: str | None = getattr(m, "id", None)
            if mid and mid in seen_ids:
                continue
            if mid:
                seen_ids.add(mid)

            content: str | list[str | dict] = m.content
            if isinstance(content, str):
                text: str = content
            else:
                text_parts: list[str] = [
                    p if isinstance(p, str) else str(p) for p in content
                ]
                text = "".join(text_parts)
            text = text.strip()
            if not text:
                continue

            role: str = "human" if isinstance(m, HumanMessage) else "ai"
            transcript.append({"role": role, "content": text})

    return transcript

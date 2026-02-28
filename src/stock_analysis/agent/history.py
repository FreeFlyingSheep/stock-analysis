"""Helpers for building chat transcripts and retrieval context from snapshots."""

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
    with tracer.start_as_current_span("chat_agent.build_chat_history") as span:
        seen_ids: set[str] = set()
        transcript: list[dict[str, str]] = []
        total_messages: int = 0
        skipped_non_chat: int = 0
        skipped_tool_calls: int = 0
        skipped_duplicates: int = 0
        skipped_empty: int = 0

        span.set_attribute("snapshot_count", len(snaps))
        for snap in snaps:
            for m in snap.values.get("messages", []):
                total_messages += 1
                if not isinstance(m, (HumanMessage, AIMessage)):
                    skipped_non_chat += 1
                    continue
                if isinstance(m, AIMessage) and getattr(m, "tool_calls", None):
                    skipped_tool_calls += 1
                    continue

                mid: str | None = getattr(m, "id", None)
                if mid and mid in seen_ids:
                    skipped_duplicates += 1
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
                    skipped_empty += 1
                    continue

                role: str = "human" if isinstance(m, HumanMessage) else "ai"
                transcript.append({"role": role, "content": text})

        span.set_attribute("messages_total", total_messages)
        span.set_attribute("messages_skipped_non_chat", skipped_non_chat)
        span.set_attribute("messages_skipped_tool_calls", skipped_tool_calls)
        span.set_attribute("messages_skipped_duplicates", skipped_duplicates)
        span.set_attribute("messages_skipped_empty", skipped_empty)
        span.set_attribute("transcript_count", len(transcript))
        return transcript

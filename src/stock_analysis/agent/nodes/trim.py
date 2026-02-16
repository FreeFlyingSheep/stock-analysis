"""Trim node to keep only the last few messages in the conversation history."""

from langchain.messages import (
    AnyMessage,  # noqa: TC002
    RemoveMessage,
)
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from opentelemetry import trace

from stock_analysis.agent.state import State  # noqa: TC001

tracer: trace.Tracer = trace.get_tracer(__name__)


def trim_messages(state: State) -> dict | None:
    """Keep only the last few messages to fit context window.

    Args:
        state: Current state containing messages.

    Returns:
        Updated state with trimmed messages or None if no trimming needed.
    """
    length: int = 30
    messages: list[AnyMessage] = state["messages"]

    with tracer.start_as_current_span("chat_agent.trim_messages") as span:
        span.set_attribute("message.count", len(messages))

        if len(messages) <= length:
            span.set_attribute("message.trimmed", value=False)
            return None

        recent_messages: list[AnyMessage] = messages[-length:]
        span.set_attribute("message.trimmed", value=True)
        span.set_attribute("message.trimmed_to", len(recent_messages))
        return {
            "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *recent_messages],
        }

"""Limits for LLM calls, tool calls, and retrieve calls in the agent."""

from stock_analysis.agent.state import State  # noqa: TC001

MAX_CHAT_CALLS: int = 20
MAX_TOOL_CALLS: int = 6
MAX_RETRIEVE_CALLS: int = 2


def llm_limit_reached(state: State) -> bool:
    """Check if the LLM call limit has been reached."""
    return state.get("chat_calls", 0) >= state.get("max_chat_calls", MAX_CHAT_CALLS)


def tool_limit_reached(state: State) -> bool:
    """Check if the tool call limit has been reached."""
    return state.get("tool_calls", 0) >= state.get("max_tool_calls", MAX_TOOL_CALLS)


def retrieve_limit_reached(state: State) -> bool:
    """Check if the retrieve call limit has been reached."""
    return state.get("retrieve_calls", 0) >= state.get(
        "max_retrieve_calls", MAX_RETRIEVE_CALLS
    )

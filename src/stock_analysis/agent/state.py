"""State for the agent graph."""

from typing import NotRequired

from langgraph.graph import MessagesState


class State(MessagesState):
    """Message state for the chat agent.

    Attributes:
        locale: Optional locale string for the conversation.
        page_context: Optional string containing relevant page context.
        chat_calls: Optional integer tracking the number of chat calls made.
        tool_calls: Optional integer tracking the number of tool calls made.
        retrieve_calls: Optional integer tracking the number of retrieve calls made.
        max_chat_calls: Optional integer specifying the maximum chat calls.
        max_tool_calls: Optional integer specifying the maximum tool calls.
        max_retrieve_calls: Optional integer specifying the maximum retrieve calls.
        disable_tools: Optional boolean indicating whether tools should be disabled.
    """

    locale: NotRequired[str]
    page_context: NotRequired[str | None]
    chat_calls: NotRequired[int]
    tool_calls: NotRequired[int]
    retrieve_calls: NotRequired[int]
    max_chat_calls: NotRequired[int]
    max_tool_calls: NotRequired[int]
    max_retrieve_calls: NotRequired[int]
    disable_tools: NotRequired[bool]
    grade_result: NotRequired[str]
    rewritten_query: NotRequired[str | None]

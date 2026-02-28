"""Helper functions for the agent implementation."""

import json
from typing import TYPE_CHECKING

from langchain.messages import (
    AIMessage,
    AnyMessage,  # noqa: TC002
    HumanMessage,
    SystemMessage,
)
from langchain_core.runnables.config import RunnableConfig  # noqa: TC002

from stock_analysis.agent.prompt import PromptManager  # noqa: TC001
from stock_analysis.agent.state import State  # noqa: TC001

if TYPE_CHECKING:
    from langchain.tools import BaseTool
    from opentelemetry import trace


class AgentError(RuntimeError):
    """Custom error class for the chat agent."""


def select_tools(
    config: RunnableConfig | None,
    *,
    include_tags: set[str] | None = None,
    exclude_tags: set[str] | None = None,
) -> list[BaseTool]:
    """Select tools based on the runnable configuration.

    Args:
        config: Runnable configuration with allowed tools.
        include_tags: Optional set of tags to include in the tool selection.
        exclude_tags: Optional set of tags to exclude from the tool selection.

    Returns:
        List of tools allowed for the current run.

    Raises:
        AgentError: If both include_tags and exclude_tags are provided.
    """
    if config is None:
        return []

    tools: list[BaseTool] = config.get("configurable", {}).get("allowed_tools") or []
    if include_tags is not None and exclude_tags is not None:
        msg: str = (
            "Cannot specify both include_tags and exclude_tags for tool selection."
        )
        raise AgentError(msg)
    if include_tags is not None:
        tools = [
            tool
            for tool in tools
            if tool.tags is not None and set(tool.tags).intersection(include_tags)
        ]
    elif exclude_tags is not None:
        tools = [
            tool
            for tool in tools
            if tool.tags is None or not set(tool.tags).intersection(exclude_tags)
        ]
    return tools


def find_last_human_content(messages: list[AnyMessage]) -> str:
    """Return the text content of the most recent HumanMessage.

    Args:
        messages: List of messages to search.

    Returns:
        Content of the last HumanMessage, or empty string if none found.
    """
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            content: str | list[str | dict] = msg.content
            return content if isinstance(content, str) else str(content)
    return ""


def is_rate_limit_error(err: Exception) -> bool:
    """Best-effort detection for provider rate-limit failures."""
    error_name: str = err.__class__.__name__.lower()
    error_text: str = str(err).lower()
    return (
        "ratelimit" in error_name
        or "rate limit" in error_text
        or "tpm limit" in error_text
        or "error code: 429" in error_text
    )


def content_preview(content: str | list[str | dict], max_len: int = 240) -> str:
    """Render a compact preview for message content."""
    text: str
    if isinstance(content, str):
        text = content
    else:
        text = "".join(part if isinstance(part, str) else str(part) for part in content)
    normalized: str = " ".join(text.split())
    return normalized[:max_len]


def truncate_tool_content(
    content: str | list[str | dict],
    *,
    max_chars: int = 12000,
) -> str:
    """Normalize and truncate tool output before adding it to chat state."""
    if isinstance(content, str):
        text: str = content
    else:
        try:
            text = json.dumps(content, ensure_ascii=False)
        except TypeError, ValueError:
            text = str(content)

    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}\n\n[truncated tool output]"


def set_llm_response_attrs(span: trace.Span, message: AnyMessage) -> None:
    """Record LLM response metadata as span attributes."""
    if not isinstance(message, AIMessage):
        span.set_attribute("llm.response_type", type(message).__name__)
        return

    preview: str = content_preview(message.content)
    tool_calls: list[dict[str, str]] = getattr(message, "tool_calls", [])
    span.set_attribute("llm.tool_call_count", len(tool_calls))
    if tool_calls:
        span.set_attribute(
            "llm.tool_names",
            [tc.get("name", "<unknown>") for tc in tool_calls],
        )
    span.set_attribute("llm.content_preview", preview)


def load_prompt(prompt_manager: PromptManager, prompt: str, locale: str) -> str:
    """Load the prompt from YAML configuration.

    Args:
        prompt_manager: The prompt manager instance.
        prompt: Name of the prompt to load (e.g., "chat", "user", "page").
        locale: Locale string to determine which prompt to load.

    Returns:
        The content of the prompt as a string.

    Raises:
        AgentError: If the prompt is not found.
    """
    try:
        return prompt_manager.get_prompt(prompt, locale)
    except KeyError as e:
        msg: str = f"Prompt not found: {e}"
        raise AgentError(msg) from e


async def build_prompt(
    prompt_manager: PromptManager,
    prompt: str,
    state: State,
    locale: str,
    *,
    query_override: str | None = None,
) -> list[AnyMessage]:
    """Build prompt messages for an LLM call.

    Locates the last HumanMessage in the conversation, wraps it
    with the user / page-context templates, and keeps all subsequent
    messages (AI responses, ToolMessages, etc.) intact so the LLM
    sees the full conversation flow.

    Args:
        prompt_manager: The prompt manager to load prompt templates.
        prompt: Base prompt name to load (e.g. "chat").
        state: Current state containing messages and locale.
        locale: Locale string to determine which prompt to load.
        query_override: Optional rewritten query that overrides the last user
            message content for this single prompt build.

    Returns:
        List of messages ready to send to the LLM.
    """
    result: list[AnyMessage] = [
        SystemMessage(content=load_prompt(prompt_manager, prompt, locale))
    ]

    state_messages: list[AnyMessage] = state["messages"]

    last_human_idx: int = -1
    for i in range(len(state_messages) - 1, -1, -1):
        if isinstance(state_messages[i], HumanMessage):
            last_human_idx = i
            break

    if last_human_idx == -1:
        result.extend(state_messages)
        return result

    result.extend(state_messages[:last_human_idx])

    last_human: AnyMessage = state_messages[last_human_idx]
    user_content: str = (
        last_human.content
        if isinstance(last_human.content, str)
        else str(last_human.content)
    )
    if query_override:
        user_content = query_override
    user: str = load_prompt(prompt_manager, "user", locale).format(query=user_content)
    page_context: str | None = state.get("page_context")
    if page_context:
        page: str = load_prompt(prompt_manager, "page", locale).format(
            context=page_context
        )
        result.append(HumanMessage(content=f"{page}\n\n{user}"))
    else:
        result.append(HumanMessage(content=user))

    result.extend(state_messages[last_human_idx + 1 :])

    return result

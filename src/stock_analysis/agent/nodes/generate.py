"""Generate node for producing the final answer."""

from typing import TYPE_CHECKING

from langchain.messages import (
    AIMessage,
    AnyMessage,  # noqa: TC002
    ToolMessage,
)
from langchain_core.runnables.config import RunnableConfig  # noqa: TC002
from opentelemetry import trace

from stock_analysis.agent.helper import (
    build_prompt,
    is_rate_limit_error,
    load_prompt,
    select_tools,
    set_llm_response_attrs,
)
from stock_analysis.agent.limit import llm_limit_reached, tool_limit_reached
from stock_analysis.agent.llm import ChatModel  # noqa: TC001
from stock_analysis.agent.prompt import PromptManager  # noqa: TC001
from stock_analysis.agent.state import State  # noqa: TC001

if TYPE_CHECKING:
    from langchain.tools import BaseTool


tracer: trace.Tracer = trace.get_tracer(__name__)


async def generate_answer(
    state: State,
    config: RunnableConfig | None,
    prompt_manager: PromptManager,
    chat: ChatModel,
) -> dict:
    """Generate the final answer, optionally with non-retrieve tools.

    When the LLM-call limit is reached a fallback message is returned
    immediately.  When the tool-call limit is reached the LLM is
    invoked without tools so it produces a plain-text response.

    Args:
        state: Current state containing messages and LLM call count.
        config: Runnable configuration with allowed tools.
        prompt_manager: PromptManager for loading error prompts.
        chat: ChatModel for generating the answer.

    Returns:
        Updated state with new message and incremented LLM call count.
    """
    with tracer.start_as_current_span("chat_agent.generate_answer") as span:
        locale: str = state.get("locale", "en-US")
        chat_calls: int = state.get("chat_calls", 0)
        tool_calls: int = state.get("tool_calls", 0)
        span.set_attribute("chat_calls", chat_calls)
        span.set_attribute("tool_calls", tool_calls)

        if llm_limit_reached(state):
            span.set_attribute("limit_reached", "llm")
            return {
                "messages": [
                    AIMessage(
                        content=load_prompt(
                            prompt_manager, "error_max_steps_best_effort", locale
                        ).strip()
                    )
                ],
            }

        messages: list[AnyMessage] = await build_prompt(
            prompt_manager, "chat", state, locale
        )
        last_message: AnyMessage = state["messages"][-1]

        disable_tools: bool = state.get("disable_tools") is True or tool_limit_reached(
            state
        )
        if isinstance(last_message, ToolMessage):
            disable_tools = True
        span.set_attribute("disable_tools", disable_tools)

        try:
            if disable_tools:
                message: AIMessage = await chat.ainvoke(messages)
            else:
                tools: list[BaseTool] = select_tools(config, exclude_tags={"retrieve"})
                span.set_attribute(
                    "available_tools",
                    [tool.name for tool in tools],
                )
                if tools:
                    try:
                        message = await chat.bind_tools(tools).ainvoke(messages)
                    except Exception as e:
                        if not is_rate_limit_error(e):
                            raise
                        span.add_event(
                            "rate_limit_fallback",
                            {"error": str(e)},
                        )
                        message = await chat.ainvoke(messages)
                else:
                    message = await chat.ainvoke(messages)
        except Exception as e:
            if not is_rate_limit_error(e):
                raise
            span.add_event("rate_limit_fallback", {"error": str(e)})
            message = AIMessage(
                content=load_prompt(
                    prompt_manager, "error_max_steps_best_effort", locale
                ).strip()
            )
        set_llm_response_attrs(span, message)

        return {
            "messages": [message],
            "locale": locale,
            "chat_calls": chat_calls + 1,
            "rewritten_query": None,
        }

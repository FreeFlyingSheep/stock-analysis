"""Route node for deciding between retrieval and direct response."""

from typing import TYPE_CHECKING

from langchain.messages import (
    AIMessage,
    AnyMessage,  # noqa: TC002
)
from langchain_core.runnables.config import RunnableConfig  # noqa: TC002
from opentelemetry import trace

from stock_analysis.agent.helper import (
    build_prompt,
    load_prompt,
    select_tools,
    set_llm_response_attrs,
)
from stock_analysis.agent.limit import llm_limit_reached, retrieve_limit_reached
from stock_analysis.agent.llm import ChatModel  # noqa: TC001
from stock_analysis.agent.prompt import PromptManager  # noqa: TC001
from stock_analysis.agent.state import State  # noqa: TC001

if TYPE_CHECKING:
    from langchain.tools import BaseTool


tracer: trace.Tracer = trace.get_tracer(__name__)


async def route_query(
    state: State,
    config: RunnableConfig | None,
    prompt_manager: PromptManager,
    chat: ChatModel,
) -> dict:
    """Decide whether to retrieve documents or respond directly.

    Uses the chat prompt with only retrieve-tagged tools bound.
    When the retrieve-call limit has already been reached the LLM is
    invoked without tools so it answers directly.

    Args:
        state: Current state containing messages and context.
        config: Runnable configuration with allowed tools.
        prompt_manager: PromptManager for loading error prompts.
        chat: ChatModel instance for invoking the LLM.

    Returns:
        Updated state with the LLM response.
    """
    with tracer.start_as_current_span("chat_agent.route_query") as span:
        locale: str = state.get("locale", "en-US")
        chat_calls: int = state.get("chat_calls", 0)
        retrieve_calls: int = state.get("retrieve_calls", 0)
        span.set_attribute("chat_calls", chat_calls)
        span.set_attribute("retrieve_calls", retrieve_calls)

        if llm_limit_reached(state):
            span.set_attribute("limit_reached", "llm")
            return {
                "messages": [
                    AIMessage(
                        content=load_prompt(
                            prompt_manager, "error_max_steps_specific", locale
                        ).strip()
                    )
                ],
            }

        rewritten_query: str | None = state.get("rewritten_query")
        if rewritten_query:
            span.set_attribute("rewritten_query", rewritten_query[:100])

        messages: list[AnyMessage] = await build_prompt(
            prompt_manager, "route", state, locale, query_override=rewritten_query
        )
        tools: list[BaseTool] = select_tools(config, include_tags={"retrieve"})
        span.set_attribute("retrieve_tools_count", len(tools))
        span.set_attribute("retrieve_tools", [tool.name for tool in tools])

        if tools and not retrieve_limit_reached(state):
            message: AnyMessage = await chat.bind_tools(tools).ainvoke(messages)
        else:
            if not tools:
                span.set_attribute("skip_reason", "no_retrieve_tools")
            else:
                span.set_attribute("skip_reason", "retrieve_limit_reached")
            message = await chat.ainvoke(messages)
        set_llm_response_attrs(span, message)

        if isinstance(message, AIMessage) and message.tool_calls:
            span.set_attribute("suggested_tool_calls", len(message.tool_calls))

        return {
            "messages": [message],
            "locale": locale,
            "chat_calls": chat_calls + 1,
        }

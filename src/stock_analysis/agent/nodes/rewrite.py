"""Rewrite node for reformulating user questions before retrieval."""

from langchain.messages import (
    AIMessage,
    AnyMessage,  # noqa: TC002
    HumanMessage,
    SystemMessage,
)
from opentelemetry import trace

from stock_analysis.agent.helper import (
    find_last_human_content,
    load_prompt,
    set_llm_response_attrs,
)
from stock_analysis.agent.limit import llm_limit_reached
from stock_analysis.agent.llm import ChatModel  # noqa: TC001
from stock_analysis.agent.prompt import PromptManager  # noqa: TC001
from stock_analysis.agent.state import State  # noqa: TC001

tracer: trace.Tracer = trace.get_tracer(__name__)


async def rewrite_question(
    state: State, prompt_manager: PromptManager, chat: ChatModel
) -> dict:
    """Rewrite the user's question for better retrieval.

    Builds a standalone rewrite prompt (not the full chat prompt) so
    the LLM focuses on query reformulation. The rewritten text is
    stored in state so the next route_query iteration can reuse it
    without adding synthetic user messages.

    Args:
        state: Current state containing messages and page context.
        prompt_manager: PromptManager for loading rewrite prompts.
        chat: ChatModel for invoking the rewrite prompt.

    Returns:
        Updated state with the rewritten query.
    """
    with tracer.start_as_current_span("chat_agent.rewrite_question") as span:
        if llm_limit_reached(state):
            span.set_attribute("limit_reached", "llm")
            locale: str = state.get("locale", "en-US")
            return {
                "messages": [
                    AIMessage(
                        content=load_prompt(
                            prompt_manager, "error_max_steps_specific", locale
                        ).strip()
                    )
                ],
            }

        locale = state.get("locale", "en-US")
        query: str = find_last_human_content(state["messages"])
        span.set_attribute("original_query", query[:100])
        span.set_attribute("has_page_context", state.get("page_context") is not None)

        page_context: str | None = state.get("page_context")
        if page_context:
            page: str = load_prompt(prompt_manager, "page", locale).format(
                context=page_context
            )
            user: str = load_prompt(prompt_manager, "user", locale).format(query=query)
            content: str = f"{page}\n\n{user}"
        else:
            content = query

        messages: list[AnyMessage] = [
            SystemMessage(content=load_prompt(prompt_manager, "rewrite", locale)),
            HumanMessage(content=content),
        ]
        rewritten: AnyMessage = await chat.ainvoke(messages)
        set_llm_response_attrs(span, rewritten)
        rewritten_text: str = (
            rewritten.content
            if isinstance(rewritten.content, str)
            else str(rewritten.content)
        )
        span.set_attribute("rewritten_query", rewritten_text[:100])

        return {
            "rewritten_query": rewritten_text,
            "locale": locale,
            "chat_calls": state.get("chat_calls", 0) + 1,
        }

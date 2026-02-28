"""Retrieve node for executing tool calls to retrieve documents."""

from typing import TYPE_CHECKING

from langchain.messages import (
    AIMessage,
    AnyMessage,  # noqa: TC002
    ToolMessage,
)
from langchain_core.runnables.config import RunnableConfig  # noqa: TC002
from opentelemetry import trace

from stock_analysis.agent.helper import load_prompt, select_tools, truncate_tool_content
from stock_analysis.agent.limit import MAX_RETRIEVE_CALLS
from stock_analysis.agent.prompt import PromptManager  # noqa: TC001
from stock_analysis.agent.state import State  # noqa: TC001

if TYPE_CHECKING:
    from langchain.tools import BaseTool

tracer: trace.Tracer = trace.get_tracer(__name__)


async def retrieve_documents(
    state: State, config: RunnableConfig | None, prompt_manager: PromptManager
) -> dict:
    """Execute retrieve tool calls.

    Args:
        state: Current state containing messages.
        config: Runnable configuration with allowed tools.
        prompt_manager: PromptManager for loading error prompts.

    Returns:
        Updated state with ToolMessages from retrieval.
    """
    with tracer.start_as_current_span("chat_agent.retrieve_documents") as span:
        result: list[ToolMessage] = []
        retrieve_calls: int = 0
        message: AnyMessage = state["messages"][-1]
        locale: str = state.get("locale", "en-US")
        current_retrieve_calls: int = state.get("retrieve_calls", 0)
        max_retrieve: int = state.get("max_retrieve_calls", MAX_RETRIEVE_CALLS)
        remaining_calls: int = max(0, max_retrieve - current_retrieve_calls)
        span.set_attribute("retrieve_calls.current", current_retrieve_calls)
        span.set_attribute("retrieve_calls.remaining", remaining_calls)

        tools: list[BaseTool] = select_tools(config, include_tags={"retrieve"})
        tools_by_name: dict[str, BaseTool] = {tool.name: tool for tool in tools}
        span.set_attribute("retrieve_tools", list(tools_by_name.keys()))

        if isinstance(message, AIMessage):
            span.set_attribute("tool_call_count", len(message.tool_calls))
            for tool_call in message.tool_calls:
                if remaining_calls <= 0:
                    span.add_event(
                        "retrieve_limit_reached",
                        {"tool_name": tool_call["name"]},
                    )
                    result.append(
                        ToolMessage(
                            content=load_prompt(
                                prompt_manager,
                                "error_retrieve_call_limit_reached",
                                locale,
                            ).strip(),
                            tool_call_id=tool_call["id"],
                        )
                    )
                    continue
                tool_name: str = tool_call["name"]
                tool: BaseTool | None = tools_by_name.get(tool_name)
                if tool is None:
                    result.append(
                        ToolMessage(
                            content=load_prompt(
                                prompt_manager, "error_tool_not_found", locale
                            )
                            .strip()
                            .format(name=tool_name),
                            tool_call_id=tool_call["id"],
                        )
                    )
                    continue
                try:
                    observation: str | list[str | dict] = await tool.ainvoke(
                        tool_call["args"]
                    )
                    span.add_event(
                        "tool_completed",
                        {
                            "tool_name": tool_name,
                            "result_preview": (
                                str(observation)[:200] if observation else "<empty>"
                            ),
                        },
                    )
                except Exception as e:  # noqa: BLE001
                    result.append(
                        ToolMessage(
                            content=load_prompt(
                                prompt_manager, "error_tool_failed", locale
                            )
                            .strip()
                            .format(name=tool_name, error=str(e)),
                            tool_call_id=tool_call["id"],
                        )
                    )
                    continue
                result.append(
                    ToolMessage(
                        content=truncate_tool_content(observation),
                        tool_call_id=tool_call["id"],
                    )
                )
                retrieve_calls += 1
                remaining_calls -= 1

        span.set_attribute("retrieve_calls.completed", retrieve_calls)
        span.set_attribute(
            "retrieve_calls.total",
            current_retrieve_calls + retrieve_calls,
        )
        return {
            "messages": result,
            "retrieve_calls": current_retrieve_calls + retrieve_calls,
        }

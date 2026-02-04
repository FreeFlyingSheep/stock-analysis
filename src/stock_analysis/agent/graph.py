"""Graph node definitions for stock analysis agent."""

from typing import TYPE_CHECKING, Annotated, NotRequired

from langchain.messages import (
    AIMessage,
    AnyMessage,  # noqa: TC002
    HumanMessage,
    RemoveMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.messages.ai import AIMessageChunk
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import REMOVE_ALL_MESSAGES, add_messages
from typing_extensions import TypedDict

from stock_analysis.agent.model import LLM, Embeddings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from langchain.messages import AIMessageChunk
    from langchain.tools import BaseTool
    from langchain_core.language_models import LanguageModelInput
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from langgraph.graph.state import CompiledStateGraph, Runnable
    from langgraph.pregel.debug import StateSnapshot


class MessagesState(TypedDict):
    """Message state for the chat agent."""

    messages: Annotated[list[AnyMessage], add_messages]
    """List of messages exchanged in the chat."""
    llm_calls: NotRequired[int]
    """Number of LLM calls made."""
    tool_calls: NotRequired[int]
    """Number of tool calls made."""


class ChatAgent:
    """Graph-based chat agent for stock analysis."""

    _llm: LLM
    _embeddings: Embeddings
    _checkpointer: AsyncPostgresSaver
    _agent: CompiledStateGraph[MessagesState, None, MessagesState, MessagesState]

    def __init__(self, checkpointer: AsyncPostgresSaver) -> None:
        """Asynchronously create the chat agent instance."""
        self._llm = LLM()
        self._embeddings = Embeddings()
        self._checkpointer = checkpointer
        self._agent = self._create_agent()

    def _trim_messages(self, state: MessagesState) -> dict | None:
        """Keep only the last few messages to fit context window.

        Args:
            state: Current state containing messages.

        Returns:
            Updated state with trimmed messages or None if no trimming needed.
        """
        length: int = 30
        messages: list[AnyMessage] = state["messages"]

        if len(messages) <= length:
            return None

        recent_messages: list[AnyMessage] = messages[-length:]
        return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *recent_messages]}

    def _select_tools(self, config: RunnableConfig | None) -> list[BaseTool]:
        if config is None:
            return []
        return config.get("configurable", {}).get("allowed_tools") or []

    async def _llm_call(
        self, state: MessagesState, config: RunnableConfig | None
    ) -> dict:
        """Invoke the LLM with the current messages.

        Args:
            state: Current state containing messages and LLM call count.
            config: Runnable configuration with allowed tools.

        Returns:
            Updated state with new message and incremented LLM call count.
        """
        tools: list[BaseTool] = self._select_tools(config)
        llm_with_tools: Runnable[LanguageModelInput, AIMessage] = self._llm.bind_tools(
            tools
        )
        messages: list[AnyMessage] = [
            SystemMessage(content="You are a helpful assistant."),
        ]
        return {
            "messages": [await llm_with_tools.ainvoke(messages + state["messages"])],
            "llm_calls": state.get("llm_calls", 0) + 1,
        }

    async def _tool_node(
        self, state: MessagesState, config: RunnableConfig | None
    ) -> dict:
        """Performs the tool call.

        Args:
            state: Current state containing messages and tool call count.
            config: Runnable configuration with allowed tools.

        Returns:
            Updated state with tool messages and incremented tool call count.
        """
        result: list[ToolMessage] = []
        tool_calls: int = 0
        message: AnyMessage = state["messages"][-1]
        tools: list[BaseTool] = self._select_tools(config)
        tools_by_name: dict[str, BaseTool] = {tool.name: tool for tool in tools}
        if isinstance(message, AIMessage):
            for tool_call in message.tool_calls:
                tool: BaseTool = tools_by_name[tool_call["name"]]
                observation: str | list[str | dict] = await tool.ainvoke(
                    tool_call["args"]
                )
                result.append(
                    ToolMessage(content=observation, tool_call_id=tool_call["id"])
                )
                tool_calls += 1
        return {
            "messages": result,
            "tool_calls": state.get("tool_calls", 0) + tool_calls,
        }

    def _should_continue(self, state: MessagesState) -> str:
        """Decide if we should continue the loop or stop.

        Args:
            state: Current state containing messages.

        Returns:
            "tool_node" if a tool call was made, otherwise END.
        """
        message: AnyMessage = state["messages"][-1]
        if isinstance(message, AIMessage) and message.tool_calls:
            return "tool_node"
        return END

    def _create_agent(
        self,
    ) -> CompiledStateGraph[MessagesState, None, MessagesState, MessagesState]:
        """Create a stock analysis agent using a graph-based approach.

        Args:
            llm: Language model instance for generating responses.
            embeddings: Embedding model instance for semantic understanding.
            tools: List of tools available to the agent.

        Returns:
            Compiled agent ready for use.
        """
        agent_builder: StateGraph[MessagesState, None, MessagesState, MessagesState] = (
            StateGraph(MessagesState)
        )
        agent_builder.add_node("trim_messages", self._trim_messages)
        agent_builder.add_node("llm_call", self._llm_call)
        agent_builder.add_node("tool_node", self._tool_node)
        agent_builder.add_edge(START, "trim_messages")
        agent_builder.add_edge("trim_messages", "llm_call")
        agent_builder.add_conditional_edges(
            "llm_call", self._should_continue, ["tool_node", END]
        )
        agent_builder.add_edge("tool_node", "llm_call")
        agent: CompiledStateGraph[MessagesState, None, MessagesState, MessagesState] = (
            agent_builder.compile(checkpointer=self._checkpointer)
        )
        return agent

    def invoke(
        self, thread_id: str, message: str, tools: list[BaseTool] | None = None
    ) -> dict:
        """Invoke the chat agent with a user message.

        Args:
            thread_id: Identifier for the chat thread.
            message: User's input message.
            tools: List of available tools.

        Returns:
            Resulting state after processing the message.
        """
        config = RunnableConfig(
            configurable={
                "thread_id": thread_id,
                "allowed_tools": tools,
            }
        )
        messages: list[AnyMessage] = [HumanMessage(content=message)]
        return self._agent.invoke({"messages": messages}, config)

    async def ainvoke(
        self, thread_id: str, message: str, tools: list[BaseTool] | None = None
    ) -> dict:
        """Asynchronously invoke the chat agent with a user message.

        Args:
            thread_id: Identifier for the chat thread.
            message: User's input message.
            tools: List of available tools.

        Returns:
            Resulting state after processing the message.
        """
        config = RunnableConfig(
            configurable={
                "thread_id": thread_id,
                "allowed_tools": tools,
            }
        )
        messages: list[AnyMessage] = [HumanMessage(content=message)]
        return await self._agent.ainvoke({"messages": messages}, config)

    async def astream_events(
        self, thread_id: str, message: str, tools: list[BaseTool] | None = None
    ) -> AsyncGenerator[str]:
        """Stream token-by-token events from the chat agent.

        Args:
            thread_id: Identifier for the chat thread.
            message: User's input message.
            tools: List of available tools.

        Yields:
            Token content for each streaming event.
        """
        config = RunnableConfig(
            configurable={
                "thread_id": thread_id,
                "allowed_tools": tools,
            }
        )
        messages: list[AnyMessage] = [HumanMessage(content=message)]
        async for event in self._agent.astream_events({"messages": messages}, config):
            kind: str = event.get("event", "")
            if kind == "on_chat_model_stream":
                chunk: AIMessageChunk | None = event.get("data", {}).get("chunk")
                if chunk and chunk.content:
                    content: str | list[str | dict] = chunk.content
                    if isinstance(content, str):
                        yield content
                    else:
                        text_parts: list[str] = [
                            p if isinstance(p, str) else str(p) for p in content
                        ]
                        yield "".join(text_parts)

    async def aget_chat_history(self, thread_id: str) -> list[dict[str, str]]:
        """Retrieve the state history for a given thread.

        Args:
            thread_id: Identifier for the chat thread.

        Returns:
            List of message states in the thread's history.
        """
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

        snaps: list[StateSnapshot] = [
            snap async for snap in self._agent.aget_state_history(config)
        ]
        snaps.reverse()

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

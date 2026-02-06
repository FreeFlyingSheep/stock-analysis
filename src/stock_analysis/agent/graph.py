"""Graph node definitions for stock analysis agent."""

from pathlib import Path
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
    import os
    from collections.abc import AsyncGenerator

    from langchain.messages import AIMessageChunk
    from langchain.tools import BaseTool
    from langchain_core.language_models import LanguageModelInput
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from langgraph.graph.state import CompiledStateGraph, Runnable
    from langgraph.pregel.debug import StateSnapshot


class AgentError(RuntimeError):
    """Custom error class for the chat agent."""


class MessagesState(TypedDict):
    """Message state for the chat agent."""

    messages: Annotated[list[AnyMessage], add_messages]
    """List of messages exchanged in the chat."""
    locale: NotRequired[str]
    """Locale for the conversation, e.g., 'en-US'."""
    page_context: NotRequired[str]
    """Optional context about the current page or topic."""
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
    _prompts_dir: Path
    _prompts: dict[str, str]

    def __init__(
        self,
        checkpointer: AsyncPostgresSaver,
        prompts_dir: str | os.PathLike[str],
        llm: LLM | None = None,
        embeddings: Embeddings | None = None,
    ) -> None:
        """Initialize the chat agent instance.

        Args:
            checkpointer: Checkpointer used for persisting agent state.
            prompts_dir: Directory containing prompt templates.
            llm: Optional language model wrapper.
            embeddings: Optional embeddings wrapper.
        """
        self._llm = llm or LLM()
        self._embeddings = embeddings or Embeddings()
        self._checkpointer = checkpointer
        self._agent = self._create_agent()
        self._prompts_dir = Path(prompts_dir)
        self._prompts: dict[str, str] = {}

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
        """Select tools based on the runnable configuration.

        Args:
            config: Runnable configuration with allowed tools.

        Returns:
            List of tools allowed for the current run.
        """
        if config is None:
            return []
        return config.get("configurable", {}).get("allowed_tools") or []

    def _load_prompt(self, prompt: str, locale: str) -> str:
        """Load the prompt from a file, caching it for future use.

        Args:
            prompt: Name of the prompt to load (e.g., "chat", "user", "page").
            locale: Locale string to determine which prompt to load.

        Returns:
            The content of the prompt file as a string.

        Raises:
            AgentError: If the prompt file does not exist.
        """
        if prompt in self._prompts:
            return self._prompts[prompt]

        if locale == "zh-CN":
            prompt_path: Path = self._prompts_dir / f"{prompt}.zh-CN.md"
        else:
            prompt_path = self._prompts_dir / f"{prompt}.md"
        if not prompt_path.exists():
            msg: str = f"Prompt file not found: {prompt_path}"
            raise AgentError(msg)

        self._prompts[prompt] = prompt_path.read_text(encoding="utf-8")
        return self._prompts[prompt]

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
        locale: str = state.get("locale", "en-US")
        messages: list[AnyMessage] = [
            SystemMessage(content=self._load_prompt("chat", locale))
        ]

        previous_messages: list[AnyMessage] = state["messages"][:-1]
        messages.extend(previous_messages)

        last_message: AnyMessage = state["messages"][-1]
        user: str = self._load_prompt("user", locale).format(query=last_message.content)
        page_context: str | None = state.get("page_context")
        if page_context:
            page: str = self._load_prompt("page", locale).format(context=page_context)
            messages.append(HumanMessage(content=f"{page}\n\n{user}"))
        else:
            messages.append(HumanMessage(content=user))

        return {
            "messages": [await llm_with_tools.ainvoke(messages)],
            "locale": locale,
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

    async def astream_events(
        self,
        thread_id: str,
        message: str,
        locale: str,
        page_context: str | None = None,
        tools: list[BaseTool] | None = None,
    ) -> AsyncGenerator[str]:
        """Stream token-by-token events from the chat agent.

        Args:
            thread_id: Identifier for the chat thread.
            message: User's input message.
            locale: Locale for the conversation.
            page_context: Optional context related to the chat.
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
        async for event in self._agent.astream_events(
            {
                "messages": messages,
                "page_context": page_context,
                "locale": locale,
            },
            config,
        ):
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

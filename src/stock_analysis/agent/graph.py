"""Graph node definitions for stock analysis agent."""

from functools import partial
from typing import TYPE_CHECKING

from langchain.messages import (
    AIMessage,
    AnyMessage,  # noqa: TC002
    HumanMessage,
)
from langchain_core.messages.ai import AIMessageChunk
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from opentelemetry import trace

from stock_analysis.agent.limit import (
    MAX_CHAT_CALLS,
    MAX_RETRIEVE_CALLS,
    MAX_TOOL_CALLS,
    llm_limit_reached,
    retrieve_limit_reached,
)
from stock_analysis.agent.llm import ChatModel, Embeddings
from stock_analysis.agent.nodes import (
    generate_answer,
    grade_documents,
    retrieve_documents,
    rewrite_question,
    route_query,
    tool_node,
    trim_messages,
)
from stock_analysis.agent.prompt import PromptManager
from stock_analysis.agent.state import State

if TYPE_CHECKING:
    import os
    from collections.abc import AsyncGenerator

    from langchain.messages import AIMessageChunk
    from langchain.tools import BaseTool
    from langchain_core.runnables.graph import Graph
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from langgraph.graph.state import CompiledStateGraph
    from langgraph.pregel.debug import StateSnapshot


tracer: trace.Tracer = trace.get_tracer(__name__)


class ChatAgent:
    """Graph-based chat agent for stock analysis."""

    _chat: ChatModel
    _embeddings: Embeddings
    _checkpointer: AsyncPostgresSaver
    _agent: CompiledStateGraph[State, None, State, State]
    _prompt_manager: PromptManager

    def __init__(
        self,
        checkpointer: AsyncPostgresSaver,
        prompts_dir: str | os.PathLike[str],
        llm: ChatModel | None = None,
        embeddings: Embeddings | None = None,
    ) -> None:
        """Initialize the chat agent instance.

        Args:
            checkpointer: Checkpointer used for persisting agent state.
            prompts_dir: Directory containing prompt templates.
            llm: Optional language model wrapper.
            embeddings: Optional embeddings wrapper.
        """
        with tracer.start_as_current_span("chat_agent.init") as span:
            span.set_attribute("prompts_dir", str(prompts_dir))
            self._chat = llm or ChatModel()
            self._embeddings = embeddings or Embeddings()
            self._checkpointer = checkpointer
            self._prompt_manager = PromptManager(prompts_dir)
            self._agent = self._create_agent()

    def get_embeddings(self) -> Embeddings:
        """Get the embeddings instance."""
        return self._embeddings

    def get_graph(self) -> Graph:
        """Get the compiled agent graph."""
        return self._agent.get_graph()

    def _should_retrieve(self, state: State) -> str:
        """Route to determine if document retrieval is needed based on the LLM response.

        Args:
            state: Current state containing messages.

        Returns:
            Next node name.
        """
        message: AnyMessage = state["messages"][-1]
        with tracer.start_as_current_span("chat_agent.should_retrieve") as span:
            if isinstance(message, AIMessage) and message.tool_calls:
                span.set_attribute("route", "retrieve_documents")
                span.set_attribute("tool_call_count", len(message.tool_calls))
                return "retrieve_documents"
            span.set_attribute("route", "generate_answer")
            return "generate_answer"

    def _after_grade(self, state: State) -> str:
        """Route after document grading.

        Returns generate_answer when documents are relevant or when
        limits have been reached; otherwise returns rewrite_question to
        retry with a reformulated query.

        Args:
            state: Current state with grade_result and counters.

        Returns:
            Next node name.
        """
        with tracer.start_as_current_span("chat_agent.after_grade") as span:
            grade_result: str | None = state.get("grade_result")
            span.set_attribute("grade_result", grade_result or "")

            if grade_result == "yes":
                span.set_attribute("route", "generate_answer")
                return "generate_answer"

            llm_limited: bool = llm_limit_reached(state)
            retrieve_limited: bool = retrieve_limit_reached(state)
            span.set_attribute("llm_limited", llm_limited)
            span.set_attribute("retrieve_limited", retrieve_limited)

            if llm_limited or retrieve_limited:
                span.set_attribute("route", "generate_answer")
                return "generate_answer"

            span.set_attribute("route", "rewrite_question")
            return "rewrite_question"

    def _should_continue(self, state: State) -> str:
        """Decide if we should continue the loop or stop.

        Args:
            state: Current state containing messages.

        Returns:
            "tool_node" if a tool call was made, otherwise END.
        """
        message: AnyMessage = state["messages"][-1]
        with tracer.start_as_current_span("chat_agent.should_continue") as span:
            if isinstance(message, AIMessage) and message.tool_calls:
                span.set_attribute("route", "tool_node")
                span.set_attribute("tool_call_count", len(message.tool_calls))
                return "tool_node"
            span.set_attribute("route", END)
            return END

    def _create_agent(
        self,
    ) -> CompiledStateGraph[State, None, State, State]:
        """Create a stock analysis agent using a graph-based approach.

        Returns:
            Compiled agent ready for use.
        """
        builder: StateGraph[State, None, State, State] = StateGraph(State)

        builder.add_node("trim_messages", trim_messages)
        builder.add_node(
            "route_query",
            partial(
                route_query,
                prompt_manager=self._prompt_manager,
                chat=self._chat,
            ),
        )
        builder.add_node(
            "retrieve_documents",
            partial(
                retrieve_documents,
                prompt_manager=self._prompt_manager,
            ),
        )
        builder.add_node(
            "grade_documents",
            partial(
                grade_documents,
                prompt_manager=self._prompt_manager,
                chat=self._chat,
            ),
        )
        builder.add_node(
            "rewrite_question",
            partial(
                rewrite_question,
                prompt_manager=self._prompt_manager,
                chat=self._chat,
            ),
        )
        builder.add_node(
            "generate_answer",
            partial(
                generate_answer,
                prompt_manager=self._prompt_manager,
                chat=self._chat,
            ),
        )
        builder.add_node(
            "tool_node",
            partial(
                tool_node,
                prompt_manager=self._prompt_manager,
            ),
        )

        builder.add_edge(START, "trim_messages")
        builder.add_edge("trim_messages", "route_query")
        builder.add_conditional_edges(
            "route_query",
            self._should_retrieve,
            ["retrieve_documents", "generate_answer"],
        )
        builder.add_edge("retrieve_documents", "grade_documents")
        builder.add_conditional_edges(
            "grade_documents",
            self._after_grade,
            ["rewrite_question", "generate_answer"],
        )
        builder.add_edge("rewrite_question", "route_query")
        builder.add_conditional_edges(
            "generate_answer",
            self._should_continue,
            ["tool_node", END],
        )
        builder.add_edge("tool_node", "generate_answer")

        agent: CompiledStateGraph[State, None, State, State] = builder.compile(
            checkpointer=self._checkpointer
        )
        return agent

    async def astream_events(  # noqa: PLR0913
        self,
        thread_id: str,
        message: str,
        locale: str,
        page_context: str | None = None,
        tools: list[BaseTool] | None = None,
        *,
        max_chat_calls: int = MAX_CHAT_CALLS,
        max_tool_calls: int = MAX_TOOL_CALLS,
        max_retrieve_calls: int = MAX_RETRIEVE_CALLS,
    ) -> AsyncGenerator[str]:
        """Stream token-by-token events from the chat agent.

        Args:
            thread_id: Identifier for the chat thread.
            message: User's input message.
            locale: Locale for the conversation.
            page_context: Optional context related to the chat.
            tools: List of available tools.
            max_chat_calls: Maximum number of LLM invocations allowed.
            max_tool_calls: Maximum number of non-retrieve tool invocations.
            max_retrieve_calls: Maximum number of retrieval invocations.

        Yields:
            Token content for each streaming event.
        """
        with tracer.start_as_current_span("chat_agent.astream_events") as span:
            span.set_attribute("thread_id", thread_id)
            span.set_attribute("locale", locale)
            span.set_attribute("has_page_context", page_context is not None)
            span.set_attribute("tools", [t.name for t in (tools or [])])
            span.set_attribute("max_chat_calls", max_chat_calls)
            span.set_attribute("max_tool_calls", max_tool_calls)
            span.set_attribute("max_retrieve_calls", max_retrieve_calls)

            config = RunnableConfig(
                configurable={
                    "thread_id": thread_id,
                    "allowed_tools": tools,
                }
            )
            messages: list[AnyMessage] = [HumanMessage(content=message)]

            token_count = 0
            async for event in self._agent.astream_events(
                {
                    "messages": messages,
                    "page_context": page_context,
                    "locale": locale,
                    "rewritten_query": None,
                    "MAX_CHAT_CALLS": MAX_CHAT_CALLS,
                    "max_tool_calls": max_tool_calls,
                    "max_retrieve_calls": max_retrieve_calls,
                },
                config,
            ):
                kind: str = event.get("event", "")
                raw_metadata: object = event.get("metadata")
                metadata: dict = raw_metadata if isinstance(raw_metadata, dict) else {}
                node_name: str | None = metadata.get("langgraph_node")

                if kind == "on_chat_model_stream" and node_name == "generate_answer":
                    chunk: AIMessageChunk | None = event.get("data", {}).get("chunk")
                    if chunk and chunk.content:
                        content: str | list[str | dict] = chunk.content
                        if isinstance(content, str):
                            token_count += len(content)
                            yield content
                        else:
                            text_parts: list[str] = [
                                p if isinstance(p, str) else str(p) for p in content
                            ]
                            text: str = "".join(text_parts)
                            token_count += len(text)
                            yield text

            span.set_attribute("total_tokens", token_count)

    async def aget_chat_history(self, thread_id: str) -> list[dict[str, str]]:
        """Retrieve the state history for a given thread.

        Args:
            thread_id: Identifier for the chat thread.

        Returns:
            List of message states in the thread's history.
        """
        with tracer.start_as_current_span("chat_agent.get_chat_history") as span:
            span.set_attribute("thread_id", thread_id)
            config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

            snaps: list[StateSnapshot] = [
                snap async for snap in self._agent.aget_state_history(config)
            ]
            span.set_attribute("snapshot_count", len(snaps))
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

            span.set_attribute("message_count", len(transcript))
            return transcript

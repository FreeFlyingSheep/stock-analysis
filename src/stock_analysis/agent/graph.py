"""Graph node definitions for stock analysis agent."""

from typing import TYPE_CHECKING, NotRequired

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
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.graph.state import CompiledStateGraph
from opentelemetry import trace
from pydantic import BaseModel, Field

from stock_analysis.agent.model import LLM, Embeddings
from stock_analysis.agent.prompts import PromptManager
from stock_analysis.logger import get_logger

if TYPE_CHECKING:
    import logging
    import os
    from collections.abc import AsyncGenerator

    from langchain.messages import AIMessageChunk
    from langchain.tools import BaseTool
    from langchain_core.runnables.graph import Graph
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from langgraph.graph.state import CompiledStateGraph
    from langgraph.pregel.debug import StateSnapshot
    from opentelemetry.trace import Span, Tracer


logger: logging.Logger = get_logger(__name__)
tracer: Tracer = trace.get_tracer(__name__)


class AgentError(RuntimeError):
    """Custom error class for the chat agent."""


class State(MessagesState):
    """Message state for the chat agent.

    Attributes:
        locale: Optional locale string for the conversation.
        page_context: Optional string containing relevant page context.
        llm_calls: Optional integer tracking the number of LLM calls made.
        tool_calls: Optional integer tracking the number of tool calls made.
        retrieve_calls: Optional integer tracking the number of retrieve calls made.
        max_llm_calls: Optional integer specifying the maximum LLM calls.
        max_tool_calls: Optional integer specifying the maximum tool calls.
        max_retrieve_calls: Optional integer specifying the maximum retrieve calls.
        disable_tools: Optional boolean indicating whether tools should be disabled.
    """

    locale: NotRequired[str]
    page_context: NotRequired[str]
    llm_calls: NotRequired[int]
    tool_calls: NotRequired[int]
    retrieve_calls: NotRequired[int]
    max_llm_calls: NotRequired[int]
    max_tool_calls: NotRequired[int]
    max_retrieve_calls: NotRequired[int]
    disable_tools: NotRequired[bool]
    grade_result: NotRequired[str]
    rewritten_query: NotRequired[str | None]


class GradeDocuments(BaseModel):
    """Grade documents using a binary score for relevance check.

    Attributes:
        binary_score: Relevance score indicating if the document is relevant or not.
    """

    binary_score: str = Field(
        description="Relevance score: 'yes' if relevant, or 'no' if not relevant"
    )


class ChatAgent:
    """Graph-based chat agent for stock analysis."""

    MAX_LLM_CALLS: int = 20
    MAX_TOOL_CALLS: int = 6
    MAX_RETRIEVE_CALLS: int = 2

    _llm: LLM
    _embeddings: Embeddings
    _checkpointer: AsyncPostgresSaver
    _agent: CompiledStateGraph[State, None, State, State]
    _prompt_manager: PromptManager

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
        with tracer.start_as_current_span("chat_agent.init") as span:
            span.set_attribute("prompts_dir", str(prompts_dir))
            self._llm = llm or LLM()
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

    def _trim_messages(self, state: State) -> dict | None:
        """Keep only the last few messages to fit context window.

        Args:
            state: Current state containing messages.

        Returns:
            Updated state with trimmed messages or None if no trimming needed.
        """
        length: int = 30
        messages: list[AnyMessage] = state["messages"]

        with tracer.start_as_current_span("chat_agent.trim_messages") as span:
            span.set_attribute("message.count", len(messages))

            if len(messages) <= length:
                span.set_attribute("message.trimmed", value=False)
                return None

            recent_messages: list[AnyMessage] = messages[-length:]
            span.set_attribute("message.trimmed", value=True)
            span.set_attribute("message.trimmed_to", len(recent_messages))
            return {
                "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *recent_messages],
            }

    def _select_tools(
        self,
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

        tools: list[BaseTool] = (
            config.get("configurable", {}).get("allowed_tools") or []
        )
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

    def _load_prompt(self, prompt: str, locale: str) -> str:
        """Load the prompt from YAML configuration.

        Args:
            prompt: Name of the prompt to load (e.g., "chat", "user", "page").
            locale: Locale string to determine which prompt to load.

        Returns:
            The content of the prompt as a string.

        Raises:
            AgentError: If the prompt is not found.
        """
        try:
            return self._prompt_manager.get_prompt(prompt, locale)
        except KeyError as e:
            msg: str = f"Prompt not found: {e}"
            raise AgentError(msg) from e

    def _find_last_human_content(self, messages: list[AnyMessage]) -> str:
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

    def _llm_limit_reached(self, state: State) -> bool:
        """Check if the LLM call limit has been reached."""
        return state.get("llm_calls", 0) >= state.get(
            "max_llm_calls", self.MAX_LLM_CALLS
        )

    def _tool_limit_reached(self, state: State) -> bool:
        """Check if the tool call limit has been reached."""
        return state.get("tool_calls", 0) >= state.get(
            "max_tool_calls", self.MAX_TOOL_CALLS
        )

    def _retrieve_limit_reached(self, state: State) -> bool:
        """Check if the retrieve call limit has been reached."""
        return state.get("retrieve_calls", 0) >= state.get(
            "max_retrieve_calls", self.MAX_RETRIEVE_CALLS
        )

    def _is_rate_limit_error(self, err: Exception) -> bool:
        """Best-effort detection for provider rate-limit failures."""
        error_name: str = err.__class__.__name__.lower()
        error_text: str = str(err).lower()
        return (
            "ratelimit" in error_name
            or "rate limit" in error_text
            or "tpm limit" in error_text
            or "error code: 429" in error_text
        )

    def _content_preview(
        self, content: str | list[str | dict], max_len: int = 240
    ) -> str:
        """Render a compact preview for message content."""
        text: str
        if isinstance(content, str):
            text = content
        else:
            text = "".join(
                part if isinstance(part, str) else str(part) for part in content
            )
        normalized: str = " ".join(text.split())
        return normalized[:max_len]

    def _set_llm_response_attrs(self, span: Span, message: AnyMessage) -> None:
        """Record LLM response metadata as span attributes."""
        if not isinstance(message, AIMessage):
            span.set_attribute("llm.response_type", type(message).__name__)
            return

        preview: str = self._content_preview(message.content)
        tool_calls: list[dict[str, str]] = getattr(message, "tool_calls", [])
        span.set_attribute("llm.tool_call_count", len(tool_calls))
        if tool_calls:
            span.set_attribute(
                "llm.tool_names",
                [tc.get("name", "<unknown>") for tc in tool_calls],
            )
        span.set_attribute("llm.content_preview", preview)

    async def _build_prompt(
        self,
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
            prompt: Base prompt name to load (e.g. "chat").
            state: Current state containing messages and locale.
            locale: Locale string to determine which prompt to load.
            query_override: Optional rewritten query that overrides the last user
                message content for this single prompt build.

        Returns:
            List of messages ready to send to the LLM.
        """
        result: list[AnyMessage] = [
            SystemMessage(content=self._load_prompt(prompt, locale))
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
        user: str = self._load_prompt("user", locale).format(query=user_content)
        page_context: str | None = state.get("page_context")
        if page_context:
            page: str = self._load_prompt("page", locale).format(context=page_context)
            result.append(HumanMessage(content=f"{page}\n\n{user}"))
        else:
            result.append(HumanMessage(content=user))

        result.extend(state_messages[last_human_idx + 1 :])

        return result

    async def _route_query(self, state: State, config: RunnableConfig | None) -> dict:
        """Decide whether to retrieve documents or respond directly.

        Uses the chat prompt with only retrieve-tagged tools bound.
        When the retrieve-call limit has already been reached the LLM is
        invoked without tools so it answers directly.

        Args:
            state: Current state containing messages and context.
            config: Runnable configuration with allowed tools.

        Returns:
            Updated state with the LLM response.
        """
        with tracer.start_as_current_span("chat_agent.route_query") as span:
            locale: str = state.get("locale", "en-US")
            llm_calls: int = state.get("llm_calls", 0)
            retrieve_calls: int = state.get("retrieve_calls", 0)
            span.set_attribute("llm_calls", llm_calls)
            span.set_attribute("retrieve_calls", retrieve_calls)

            if self._llm_limit_reached(state):
                span.set_attribute("limit_reached", "llm")
                return {
                    "messages": [
                        AIMessage(
                            content=self._load_prompt(
                                "error_max_steps_specific", locale
                            ).strip()
                        )
                    ],
                }

            rewritten_query: str | None = state.get("rewritten_query")
            if rewritten_query:
                span.set_attribute("rewritten_query", rewritten_query[:100])

            messages: list[AnyMessage] = await self._build_prompt(
                "route", state, locale, query_override=rewritten_query
            )
            tools: list[BaseTool] = self._select_tools(
                config, include_tags={"retrieve"}
            )
            span.set_attribute("retrieve_tools_count", len(tools))
            span.set_attribute("retrieve_tools", [tool.name for tool in tools])

            if tools and not self._retrieve_limit_reached(state):
                message: AnyMessage = await self._llm.bind_tools(tools).ainvoke(
                    messages
                )
            else:
                if not tools:
                    span.set_attribute("skip_reason", "no_retrieve_tools")
                else:
                    span.set_attribute("skip_reason", "retrieve_limit_reached")
                message = await self._llm.ainvoke(messages)
            self._set_llm_response_attrs(span, message)

            if isinstance(message, AIMessage) and message.tool_calls:
                span.set_attribute("suggested_tool_calls", len(message.tool_calls))
            else:
                # Avoid carrying a speculative router free-text response into
                # generate_answer where it can suppress subsequent tool calls.
                message = AIMessage(content="")

            return {
                "messages": [message],
                "locale": locale,
                "llm_calls": llm_calls + 1,
            }

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

    async def _retrieve_documents(
        self, state: State, config: RunnableConfig | None
    ) -> dict:
        """Execute retrieve tool calls.

        Args:
            state: Current state containing messages.
            config: Runnable configuration with allowed tools.

        Returns:
            Updated state with ToolMessages from retrieval.
        """
        with tracer.start_as_current_span("chat_agent.retrieve_documents") as span:
            result: list[ToolMessage] = []
            retrieve_calls: int = 0
            message: AnyMessage = state["messages"][-1]
            locale: str = state.get("locale", "en-US")
            current_retrieve_calls: int = state.get("retrieve_calls", 0)
            max_retrieve: int = state.get("max_retrieve_calls", self.MAX_RETRIEVE_CALLS)
            remaining_calls: int = max(0, max_retrieve - current_retrieve_calls)
            span.set_attribute("retrieve_calls.current", current_retrieve_calls)
            span.set_attribute("retrieve_calls.remaining", remaining_calls)

            tools: list[BaseTool] = self._select_tools(
                config, include_tags={"retrieve"}
            )
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
                                content=self._load_prompt(
                                    "error_retrieve_call_limit_reached", locale
                                ).strip(),
                                tool_call_id=tool_call["id"],
                            )
                        )
                        continue
                    tool_name: str = tool_call["name"]
                    tool: BaseTool | None = tools_by_name.get(tool_name)
                    if tool is None:
                        logger.error("Tool not found: %s", tool_name)
                        result.append(
                            ToolMessage(
                                content=self._load_prompt(
                                    "error_tool_not_found", locale
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
                    except Exception as e:
                        logger.exception("Retrieve tool %s failed", tool_name)
                        result.append(
                            ToolMessage(
                                content=self._load_prompt("error_tool_failed", locale)
                                .strip()
                                .format(name=tool_name, error=str(e)),
                                tool_call_id=tool_call["id"],
                            )
                        )
                        continue
                    result.append(
                        ToolMessage(content=observation, tool_call_id=tool_call["id"])
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

    async def _grade_documents(self, state: State) -> dict:
        """Grade retrieved documents for relevance using a dedicated prompt.

        Extracts the user query and the retrieved ToolMessage contents,
        builds a grading prompt, and stores the binary result in state.

        Args:
            state: Current state containing messages.

        Returns:
            Updated state with grade_result and incremented llm_calls.
        """
        with tracer.start_as_current_span("chat_agent.grade_documents") as span:
            locale: str = state.get("locale", "en-US")
            query: str = self._find_last_human_content(state["messages"])
            span.set_attribute("query_preview", query[:100])

            retrieved_parts: list[str] = []
            for msg in reversed(state["messages"]):
                if isinstance(msg, ToolMessage):
                    content: str | list[str | dict] = msg.content
                    retrieved_parts.append(
                        content if isinstance(content, str) else str(content)
                    )
                elif isinstance(msg, AIMessage):
                    break
            span.set_attribute("retrieved_document_count", len(retrieved_parts))

            retrieved: str = (
                "\n\n".join(reversed(retrieved_parts))
                or self._load_prompt("grade_no_documents", locale).strip()
            )
            grade_input: str = self._load_prompt("grade_input", locale).format(
                question=query, documents=retrieved
            )

            messages: list[AnyMessage] = [
                SystemMessage(content=self._load_prompt("grade", locale)),
                HumanMessage(content=grade_input),
            ]
            response: dict | BaseModel = await self._llm.with_structured_output(
                GradeDocuments
            ).ainvoke(messages)
            score: str = GradeDocuments.model_validate(response).binary_score
            span.set_attribute("grade_result", score)

            return {
                "grade_result": score,
                "llm_calls": state.get("llm_calls", 0) + 1,
            }

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

            llm_limited: bool = self._llm_limit_reached(state)
            retrieve_limited: bool = self._retrieve_limit_reached(state)
            span.set_attribute("llm_limited", llm_limited)
            span.set_attribute("retrieve_limited", retrieve_limited)

            if llm_limited or retrieve_limited:
                span.set_attribute("route", "generate_answer")
                return "generate_answer"

            span.set_attribute("route", "rewrite_question")
            return "rewrite_question"

    async def _rewrite_question(self, state: State) -> dict:
        """Rewrite the user's question for better retrieval.

        Builds a standalone rewrite prompt (not the full chat prompt) so
        the LLM focuses on query reformulation. The rewritten text is
        stored in state so the next route_query iteration can reuse it
        without adding synthetic user messages.

        Args:
            state: Current state containing messages and page context.

        Returns:
            Updated state with the rewritten query.
        """
        with tracer.start_as_current_span("chat_agent.rewrite_question") as span:
            if self._llm_limit_reached(state):
                span.set_attribute("limit_reached", "llm")
                locale: str = state.get("locale", "en-US")
                return {
                    "messages": [
                        AIMessage(
                            content=self._load_prompt(
                                "error_max_steps_specific", locale
                            ).strip()
                        )
                    ],
                }

            locale = state.get("locale", "en-US")
            query: str = self._find_last_human_content(state["messages"])
            span.set_attribute("original_query", query[:100])
            span.set_attribute(
                "has_page_context", state.get("page_context") is not None
            )

            page_context: str | None = state.get("page_context")
            if page_context:
                page: str = self._load_prompt("page", locale).format(
                    context=page_context
                )
                user: str = self._load_prompt("user", locale).format(query=query)
                content: str = f"{page}\n\n{user}"
            else:
                content = query

            messages: list[AnyMessage] = [
                SystemMessage(content=self._load_prompt("rewrite", locale)),
                HumanMessage(content=content),
            ]
            rewritten: AnyMessage = await self._llm.ainvoke(messages)
            self._set_llm_response_attrs(span, rewritten)
            rewritten_text: str = (
                rewritten.content
                if isinstance(rewritten.content, str)
                else str(rewritten.content)
            )
            span.set_attribute("rewritten_query", rewritten_text[:100])

            return {
                "rewritten_query": rewritten_text,
                "locale": locale,
                "llm_calls": state.get("llm_calls", 0) + 1,
            }

    async def _generate_answer(
        self, state: State, config: RunnableConfig | None
    ) -> dict:
        """Generate the final answer, optionally with non-retrieve tools.

        When the LLM-call limit is reached a fallback message is returned
        immediately.  When the tool-call limit is reached the LLM is
        invoked without tools so it produces a plain-text response.

        Args:
            state: Current state containing messages and LLM call count.
            config: Runnable configuration with allowed tools.

        Returns:
            Updated state with new message and incremented LLM call count.
        """
        with tracer.start_as_current_span("chat_agent.generate_answer") as span:
            locale: str = state.get("locale", "en-US")
            llm_calls: int = state.get("llm_calls", 0)
            tool_calls: int = state.get("tool_calls", 0)
            span.set_attribute("llm_calls", llm_calls)
            span.set_attribute("tool_calls", tool_calls)

            if self._llm_limit_reached(state):
                span.set_attribute("limit_reached", "llm")
                return {
                    "messages": [
                        AIMessage(
                            content=self._load_prompt(
                                "error_max_steps_best_effort", locale
                            ).strip()
                        )
                    ],
                }

            messages: list[AnyMessage] = await self._build_prompt("chat", state, locale)
            last_message: AnyMessage = state["messages"][-1]

            disable_tools: bool = state.get(
                "disable_tools"
            ) is True or self._tool_limit_reached(state)
            if isinstance(last_message, ToolMessage):
                disable_tools = True
            span.set_attribute("disable_tools", disable_tools)

            try:
                if disable_tools:
                    message: AIMessage = await self._llm.ainvoke(messages)
                else:
                    tools: list[BaseTool] = self._select_tools(
                        config, exclude_tags={"retrieve"}
                    )
                    span.set_attribute(
                        "available_tools",
                        [tool.name for tool in tools],
                    )
                    if tools:
                        try:
                            message = await self._llm.bind_tools(tools).ainvoke(
                                messages
                            )
                        except Exception as e:
                            if not self._is_rate_limit_error(e):
                                raise
                            span.add_event(
                                "rate_limit_fallback",
                                {"error": str(e)},
                            )
                            message = await self._llm.ainvoke(messages)
                    else:
                        message = await self._llm.ainvoke(messages)
            except Exception as e:
                if not self._is_rate_limit_error(e):
                    raise
                span.add_event("rate_limit_fallback", {"error": str(e)})
                message = AIMessage(
                    content=self._load_prompt(
                        "error_max_steps_best_effort", locale
                    ).strip()
                )
            self._set_llm_response_attrs(span, message)

            return {
                "messages": [message],
                "locale": locale,
                "llm_calls": llm_calls + 1,
                "rewritten_query": None,
            }

    async def _tool_node(self, state: State, config: RunnableConfig | None) -> dict:
        """Execute non-retrieve tool calls.

        Args:
            state: Current state containing messages and tool call count.
            config: Runnable configuration with allowed tools.

        Returns:
            Updated state with tool messages and incremented tool call count.
        """
        with tracer.start_as_current_span("chat_agent.tool_node") as span:
            result: list[ToolMessage] = []
            tool_calls_count: int = 0
            message: AnyMessage = state["messages"][-1]
            locale: str = state.get("locale", "en-US")
            current_tool_calls: int = state.get("tool_calls", 0)
            max_tool_calls: int = state.get("max_tool_calls", self.MAX_TOOL_CALLS)
            remaining_calls: int = max(0, max_tool_calls - current_tool_calls)
            span.set_attribute("tool_calls.current", current_tool_calls)
            span.set_attribute("tool_calls.remaining", remaining_calls)

            tools: list[BaseTool] = self._select_tools(config)
            tools_by_name: dict[str, BaseTool] = {tool.name: tool for tool in tools}
            span.set_attribute("available_tools", list(tools_by_name.keys()))

            if isinstance(message, AIMessage):
                span.set_attribute("tool_call_count", len(message.tool_calls))
                for tool_call in message.tool_calls:
                    if remaining_calls <= 0:
                        span.add_event(
                            "tool_limit_reached",
                            {"tool_name": tool_call["name"]},
                        )
                        result.append(
                            ToolMessage(
                                content=self._load_prompt(
                                    "error_tool_call_limit_reached", locale
                                ).strip(),
                                tool_call_id=tool_call["id"],
                            )
                        )
                        continue
                    tool_name: str = tool_call["name"]
                    tool: BaseTool | None = tools_by_name.get(tool_name)
                    if tool is None:
                        logger.error("Tool not found: %s", tool_name)
                        result.append(
                            ToolMessage(
                                content=self._load_prompt(
                                    "error_tool_not_found", locale
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
                    except Exception as e:
                        logger.exception("Tool %s failed", tool_name)
                        result.append(
                            ToolMessage(
                                content=self._load_prompt("error_tool_failed", locale)
                                .strip()
                                .format(name=tool_name, error=str(e)),
                                tool_call_id=tool_call["id"],
                            )
                        )
                        continue
                    result.append(
                        ToolMessage(content=observation, tool_call_id=tool_call["id"])
                    )
                    tool_calls_count += 1
                    remaining_calls -= 1

            span.set_attribute("tool_calls.completed", tool_calls_count)
            span.set_attribute(
                "tool_calls.total",
                current_tool_calls + tool_calls_count,
            )
            return {
                "messages": result,
                "tool_calls": current_tool_calls + tool_calls_count,
            }

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

        builder.add_node("trim_messages", self._trim_messages)
        builder.add_node("route_query", self._route_query)
        builder.add_node("retrieve_documents", self._retrieve_documents)
        builder.add_node("grade_documents", self._grade_documents)
        builder.add_node("rewrite_question", self._rewrite_question)
        builder.add_node("generate_answer", self._generate_answer)
        builder.add_node("tool_node", self._tool_node)

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
        max_llm_calls: int = MAX_LLM_CALLS,
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
            max_llm_calls: Maximum number of LLM invocations allowed.
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
            span.set_attribute("max_llm_calls", max_llm_calls)
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
                    "max_llm_calls": max_llm_calls,
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

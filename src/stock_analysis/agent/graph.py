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


logger: logging.Logger = get_logger(__name__)


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
        logger.info("[__init__] Initializing ChatAgent")
        self._llm = llm or LLM()
        logger.debug("[__init__] LLM initialized")
        self._embeddings = embeddings or Embeddings()
        logger.debug("[__init__] Embeddings initialized")
        self._checkpointer = checkpointer
        logger.debug("[__init__] Checkpointer configured")
        self._prompt_manager = PromptManager(prompts_dir)
        logger.info(
            "[__init__] Prompt manager initialized with directory: %s", prompts_dir
        )
        self._agent = self._create_agent()
        logger.info("[__init__] ChatAgent initialized successfully")

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

        logger.info("[trim_messages] Total messages count: %d", len(messages))

        if len(messages) <= length:
            logger.debug(
                "[trim_messages] Message count %d <= %d, no trimming needed",
                len(messages),
                length,
            )
            return None

        recent_messages: list[AnyMessage] = messages[-length:]
        logger.info(
            "[trim_messages] Trimmed to last %d messages from %d",
            len(recent_messages),
            len(messages),
        )
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

    def _log_llm_response(self, node: str, message: AnyMessage) -> None:
        """Log LLM response summary including tool calls and content preview."""
        if not isinstance(message, AIMessage):
            logger.info("[%s] LLM response type=%s", node, type(message).__name__)
            return

        preview: str = self._content_preview(message.content)
        tool_calls: list[dict[str, str]] = getattr(message, "tool_calls", [])
        if tool_calls:
            tool_names: list[str] = [tc.get("name", "<unknown>") for tc in tool_calls]
            logger.info(
                "[%s] LLM response tool_calls=%s names=%s content_preview=%s",
                node,
                len(tool_calls),
                tool_names,
                preview,
            )
        else:
            logger.info(
                "[%s] LLM response tool_calls=0 content_preview=%s",
                node,
                preview,
            )

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

        logger.debug(
            "[build_prompt] prompt=%s locale=%s total_messages=%s",
            prompt,
            locale,
            len(result),
        )
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
        logger.info("[route_query] Starting query routing")
        locale: str = state.get("locale", "en-US")
        llm_calls: int = state.get("llm_calls", 0)
        retrieve_calls: int = state.get("retrieve_calls", 0)
        logger.debug(
            "[route_query] Current calls - LLM: %s, Retrieve: %s",
            llm_calls,
            retrieve_calls,
        )

        if self._llm_limit_reached(state):
            max_llm: int = state.get("max_llm_calls", self.MAX_LLM_CALLS)
            logger.warning(
                "[route_query] LLM call limit reached (%s/%s)", llm_calls, max_llm
            )
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
            logger.debug(
                "[route_query] Using rewritten query: %s...", rewritten_query[:100]
            )

        messages: list[AnyMessage] = await self._build_prompt(
            "route", state, locale, query_override=rewritten_query
        )
        tools: list[BaseTool] = self._select_tools(config, include_tags={"retrieve"})
        logger.info("[route_query] Available retrieve tools: %s", len(tools))
        logger.debug("[route_query] Tools: %s", [tool.name for tool in tools])

        if tools and not self._retrieve_limit_reached(state):
            logger.info("[route_query] Invoking LLM with %s retrieve tools", len(tools))
            message: AnyMessage = await self._llm.bind_tools(tools).ainvoke(messages)
        else:
            if not tools:
                logger.debug("[route_query] No retrieve tools available")
            else:
                max_retrieve: int = state.get(
                    "max_retrieve_calls", self.MAX_RETRIEVE_CALLS
                )
                logger.debug(
                    "[route_query] Retrieve limit reached (%s/%s)",
                    retrieve_calls,
                    max_retrieve,
                )
            logger.info("[route_query] Invoking LLM without retrieve tools")
            message = await self._llm.ainvoke(messages)
        self._log_llm_response("route_query", message)

        if isinstance(message, AIMessage) and message.tool_calls:
            logger.info(
                "[route_query] LLM suggested %s tool calls", len(message.tool_calls)
            )
        else:
            logger.info("[route_query] LLM did not suggest any tool calls")
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
        if isinstance(message, AIMessage) and message.tool_calls:
            logger.info(
                "[should_retrieve] Routing to retrieve_documents (%s tool calls)",
                len(message.tool_calls),
            )
            return "retrieve_documents"
        logger.info(
            "[should_retrieve] No retrieve tools called, routing to generate_answer"
        )
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
        logger.info("[retrieve_documents] Starting document retrieval")
        result: list[ToolMessage] = []
        retrieve_calls: int = 0
        message: AnyMessage = state["messages"][-1]
        locale: str = state.get("locale", "en-US")
        current_retrieve_calls: int = state.get("retrieve_calls", 0)
        max_retrieve: int = state.get("max_retrieve_calls", self.MAX_RETRIEVE_CALLS)
        remaining_calls: int = max(0, max_retrieve - current_retrieve_calls)
        logger.debug(
            "[retrieve_documents] Retrieve calls - Current: %s, Remaining: %s",
            current_retrieve_calls,
            remaining_calls,
        )

        tools: list[BaseTool] = self._select_tools(config, include_tags={"retrieve"})
        tools_by_name: dict[str, BaseTool] = {tool.name: tool for tool in tools}
        logger.info(
            "[retrieve_documents] Available retrieve tools: %s",
            list(tools_by_name.keys()),
        )

        if isinstance(message, AIMessage):
            logger.info(
                "[retrieve_documents] Processing %s tool calls", len(message.tool_calls)
            )
            for idx, tool_call in enumerate(message.tool_calls):
                logger.debug(
                    "[retrieve_documents] Tool call %s/%s: %s",
                    idx + 1,
                    len(message.tool_calls),
                    tool_call["name"],
                )

                if remaining_calls <= 0:
                    logger.warning(
                        (
                            "[retrieve_documents] Retrieve limit reached, "
                            "skipping tool call %s"
                        ),
                        tool_call["name"],
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
                    logger.error("[retrieve_documents] Tool not found: %s", tool_name)
                    result.append(
                        ToolMessage(
                            content=self._load_prompt("error_tool_not_found", locale)
                            .strip()
                            .format(name=tool_name),
                            tool_call_id=tool_call["id"],
                        )
                    )
                    continue
                try:
                    logger.info(
                        "[retrieve_documents] Executing tool: %s with args: %s",
                        tool_name,
                        tool_call["args"],
                    )
                    observation: str | list[str | dict] = await tool.ainvoke(
                        tool_call["args"]
                    )
                    obs_preview: str = (
                        str(observation)[:200] if observation else "<empty>"
                    )
                    logger.info(
                        "[retrieve_documents] Tool %s completed. Result: %s...",
                        tool_name,
                        obs_preview,
                    )
                except Exception as e:
                    logger.exception("[retrieve_documents] Tool %s failed", tool_name)
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
        else:
            logger.warning(
                "[retrieve_documents] Last message is not AIMessage, skipping retrieval"
            )

        logger.info(
            "[retrieve_documents] Completed %s successful retrieve calls",
            retrieve_calls,
        )
        logger.info(
            "[retrieve_documents] Completed node with total_retrieve_calls=%s",
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
        logger.info("[grade_documents] Starting document grading")
        locale: str = state.get("locale", "en-US")
        query: str = self._find_last_human_content(state["messages"])
        logger.debug("[grade_documents] User query: %s...", query[:100])

        retrieved_parts: list[str] = []
        for msg in reversed(state["messages"]):
            if isinstance(msg, ToolMessage):
                content: str | list[str | dict] = msg.content
                retrieved_parts.append(
                    content if isinstance(content, str) else str(content)
                )
            elif isinstance(msg, AIMessage):
                break
        logger.debug(
            "[grade_documents] Found %s retrieved documents", len(retrieved_parts)
        )

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
        logger.info("[grade_documents] Invoking LLM for document grading")
        response: dict | BaseModel = await self._llm.with_structured_output(
            GradeDocuments
        ).ainvoke(messages)
        logger.info("[grade_documents] LLM grading raw response: %s", response)
        score: str = GradeDocuments.model_validate(response).binary_score
        logger.info("[grade_documents] Grading result: %s", score)

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
        grade_result: str | None = state.get("grade_result")
        logger.info("[after_grade] Grading result: %s", grade_result)

        if grade_result == "yes":
            logger.info(
                "[after_grade] Documents are relevant, proceeding to generate_answer"
            )
            return "generate_answer"

        llm_limited: bool = self._llm_limit_reached(state)
        retrieve_limited: bool = self._retrieve_limit_reached(state)
        logger.debug(
            "[after_grade] Limits reached - LLM: %s, Retrieve: %s",
            llm_limited,
            retrieve_limited,
        )

        if llm_limited or retrieve_limited:
            logger.info("[after_grade] Limits reached, proceeding to generate_answer")
            return "generate_answer"

        logger.info(
            "[after_grade] Documents not relevant and limits not reached, "
            "rewriting question"
        )
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
        logger.info("[rewrite_question] Starting question rewrite")
        if self._llm_limit_reached(state):
            logger.warning(
                "[rewrite_question] LLM call limit reached, returning error message"
            )
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
        logger.debug("[rewrite_question] Original query: %s...", query[:100])

        page_context: str | None = state.get("page_context")
        if page_context:
            logger.debug(
                "[rewrite_question] Page context available: %s...", page_context[:100]
            )
            page: str = self._load_prompt("page", locale).format(context=page_context)
            user: str = self._load_prompt("user", locale).format(query=query)
            content: str = f"{page}\n\n{user}"
        else:
            logger.debug("[rewrite_question] No page context available")
            content = query

        messages: list[AnyMessage] = [
            SystemMessage(content=self._load_prompt("rewrite", locale)),
            HumanMessage(content=content),
        ]
        logger.info("[rewrite_question] Invoking LLM to rewrite question")
        rewritten: AnyMessage = await self._llm.ainvoke(messages)
        self._log_llm_response("rewrite_question", rewritten)
        rewritten_text: str = (
            rewritten.content
            if isinstance(rewritten.content, str)
            else str(rewritten.content)
        )
        logger.info("[rewrite_question] Rewritten query: %s...", rewritten_text[:100])

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
        logger.info("[generate_answer] Starting answer generation")
        locale: str = state.get("locale", "en-US")
        llm_calls: int = state.get("llm_calls", 0)
        tool_calls: int = state.get("tool_calls", 0)
        logger.debug(
            "[generate_answer] Call counts - LLM: %s, Tool: %s", llm_calls, tool_calls
        )

        if self._llm_limit_reached(state):
            logger.warning(
                "[generate_answer] LLM call limit reached (%s/%s)",
                llm_calls,
                state.get("max_llm_calls", self.MAX_LLM_CALLS),
            )
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

        try:
            if disable_tools:
                logger.info(
                    "[generate_answer] Tools are disabled or limit reached, "
                    "invoking LLM without tools"
                )
                message: AIMessage = await self._llm.ainvoke(messages)
            else:
                tools: list[BaseTool] = self._select_tools(
                    config, exclude_tags={"retrieve"}
                )
                logger.info(
                    "[generate_answer] Available non-retrieve tools: %s",
                    [tool.name for tool in tools],
                )
                if tools:
                    logger.info(
                        "[generate_answer] Invoking LLM with %s tools", len(tools)
                    )
                    try:
                        message = await self._llm.bind_tools(tools).ainvoke(messages)
                    except Exception as e:
                        if not self._is_rate_limit_error(e):
                            raise
                        logger.warning(
                            "[generate_answer] Tool-bound LLM call rate-limited, "
                            "falling back to no-tools generation: %s",
                            e,
                        )
                        message = await self._llm.ainvoke(messages)
                else:
                    logger.debug("[generate_answer] No non-retrieve tools available")
                    message = await self._llm.ainvoke(messages)
        except Exception as e:
            if not self._is_rate_limit_error(e):
                raise
            logger.warning(
                "[generate_answer] LLM rate-limited, returning best-effort "
                "fallback message: %s",
                e,
            )
            message = AIMessage(
                content=self._load_prompt("error_max_steps_best_effort", locale).strip()
            )
        self._log_llm_response("generate_answer", message)

        if isinstance(message, AIMessage) and message.tool_calls:
            logger.info(
                "[generate_answer] LLM suggested %s tool calls", len(message.tool_calls)
            )
        else:
            logger.info(
                "[generate_answer] LLM generated final answer without tool calls"
            )

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
        logger.info("[tool_node] Starting tool execution")
        result: list[ToolMessage] = []
        tool_calls_count: int = 0
        message: AnyMessage = state["messages"][-1]
        locale: str = state.get("locale", "en-US")
        current_tool_calls: int = state.get("tool_calls", 0)
        max_tool_calls: int = state.get("max_tool_calls", self.MAX_TOOL_CALLS)
        remaining_calls: int = max(0, max_tool_calls - current_tool_calls)
        logger.debug(
            "[tool_node] Tool calls - Current: %s, Remaining: %s",
            current_tool_calls,
            remaining_calls,
        )

        tools: list[BaseTool] = self._select_tools(config)
        tools_by_name: dict[str, BaseTool] = {tool.name: tool for tool in tools}
        logger.info("[tool_node] Available tools: %s", list(tools_by_name.keys()))

        if isinstance(message, AIMessage):
            logger.info("[tool_node] Processing %s tool calls", len(message.tool_calls))
            for idx, tool_call in enumerate(message.tool_calls):
                logger.debug(
                    "[tool_node] Tool call %s/%s: %s",
                    idx + 1,
                    len(message.tool_calls),
                    tool_call["name"],
                )

                if remaining_calls <= 0:
                    logger.warning(
                        "[tool_node] Tool call limit reached, skipping tool call %s",
                        tool_call["name"],
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
                    logger.error("[tool_node] Tool not found: %s", tool_name)
                    result.append(
                        ToolMessage(
                            content=self._load_prompt("error_tool_not_found", locale)
                            .strip()
                            .format(name=tool_name),
                            tool_call_id=tool_call["id"],
                        )
                    )
                    continue
                try:
                    logger.info(
                        "[tool_node] Executing tool: %s with args: %s",
                        tool_name,
                        tool_call["args"],
                    )
                    observation: str | list[str | dict] = await tool.ainvoke(
                        tool_call["args"]
                    )
                    obs_preview: str = (
                        str(observation)[:200] if observation else "<empty>"
                    )
                    logger.info(
                        "[tool_node] Tool %s completed. Result: %s...",
                        tool_name,
                        obs_preview,
                    )
                except Exception as e:
                    logger.exception("[tool_node] Tool %s failed", tool_name)
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
        else:
            logger.warning(
                "[tool_node] Last message is not AIMessage, skipping tool execution"
            )

        logger.info("[tool_node] Completed %s successful tool calls", tool_calls_count)
        logger.info(
            "[tool_node] Completed node with total_tool_calls=%s",
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
        if isinstance(message, AIMessage) and message.tool_calls:
            logger.info(
                "[should_continue] Tool calls detected (%s), continuing to tool_node",
                len(message.tool_calls),
            )
            return "tool_node"
        logger.info("[should_continue] No tool calls, ending conversation")
        return END

    def _create_agent(
        self,
    ) -> CompiledStateGraph[State, None, State, State]:
        """Create a stock analysis agent using a graph-based approach.

        Returns:
            Compiled agent ready for use.
        """
        logger.info("[_create_agent] Building state graph")
        builder: StateGraph[State, None, State, State] = StateGraph(State)

        logger.debug("[_create_agent] Adding nodes to graph")
        builder.add_node("trim_messages", self._trim_messages)
        builder.add_node("route_query", self._route_query)
        builder.add_node("retrieve_documents", self._retrieve_documents)
        builder.add_node("grade_documents", self._grade_documents)
        builder.add_node("rewrite_question", self._rewrite_question)
        builder.add_node("generate_answer", self._generate_answer)
        builder.add_node("tool_node", self._tool_node)
        logger.debug("[_create_agent] 7 nodes added to graph")

        logger.debug("[_create_agent] Adding edges to graph")
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
        logger.debug("[_create_agent] Graph edges configured")

        logger.info("[_create_agent] Compiling agent graph")
        agent: CompiledStateGraph[State, None, State, State] = builder.compile(
            checkpointer=self._checkpointer
        )
        logger.info("[_create_agent] Agent graph compiled successfully")
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
        logger.info(
            "[astream_events] Starting event streaming for thread: %s", thread_id
        )
        logger.debug("[astream_events] Input message: %s...", message[:100])
        logger.debug(
            "[astream_events] Locale: %s, Page context: %s",
            locale,
            page_context is not None,
        )
        logger.debug(
            "[astream_events] Tools: %s, Limits - LLM: %s, Tool: %s, Retrieve: %s",
            [t.name for t in (tools or [])],
            max_llm_calls,
            max_tool_calls,
            max_retrieve_calls,
        )

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

        logger.info(
            "[astream_events] Event streaming completed for thread: %s, "
            "total tokens: %s",
            thread_id,
            token_count,
        )

    async def aget_chat_history(self, thread_id: str) -> list[dict[str, str]]:
        """Retrieve the state history for a given thread.

        Args:
            thread_id: Identifier for the chat thread.

        Returns:
            List of message states in the thread's history.
        """
        logger.info(
            "[aget_chat_history] Retrieving chat history for thread: %s", thread_id
        )
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

        logger.debug("[aget_chat_history] Fetching state history from checkpointer")
        snaps: list[StateSnapshot] = [
            snap async for snap in self._agent.aget_state_history(config)
        ]
        logger.info("[aget_chat_history] Retrieved %s state snapshots", len(snaps))
        snaps.reverse()

        seen_ids: set[str] = set()
        transcript: list[dict[str, str]] = []

        for snap in snaps:
            for m in snap.values.get("messages", []):
                if not isinstance(m, (HumanMessage, AIMessage)):
                    continue

                mid: str | None = getattr(m, "id", None)
                if mid and mid in seen_ids:
                    logger.debug(
                        "[aget_chat_history] Skipping duplicate message ID: %s", mid
                    )
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
                    logger.debug("[aget_chat_history] Skipping empty message")
                    continue

                role: str = "human" if isinstance(m, HumanMessage) else "ai"
                transcript.append({"role": role, "content": text})

        logger.info(
            "[aget_chat_history] Chat history completed with %s messages",
            len(transcript),
        )
        return transcript

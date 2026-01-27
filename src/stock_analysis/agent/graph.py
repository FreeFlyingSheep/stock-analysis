"""Graph node definitions for stock analysis agent."""

import operator
from typing import TYPE_CHECKING, Annotated

from langchain.messages import AIMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from stock_analysis.agent.model import LLM, Embeddings

if TYPE_CHECKING:
    from langchain.messages import AnyMessage
    from langchain.tools import BaseTool
    from langgraph.graph.state import CompiledStateGraph


class MessagesState(TypedDict):
    """Message state for the chat agent."""

    messages: Annotated[list[AnyMessage], operator.add]
    """List of messages exchanged in the chat."""
    llm_calls: int
    """Number of LLM calls made."""
    tool_calls: int
    """Number of tool calls made."""


class ChatAgent:
    """Graph-based chat agent for stock analysis."""

    _llm: LLM
    _embeddings: Embeddings
    _tools: list[BaseTool]
    _tools_by_name: dict[str, BaseTool]
    _agent: CompiledStateGraph[MessagesState, None, MessagesState, MessagesState]

    def __init__(self, tools: list[BaseTool]) -> None:
        """Initialize the chat agent."""
        self._llm = LLM(tools)
        self._embeddings = Embeddings()
        self._tools = tools
        self._tools_by_name = {tool.name: tool for tool in tools}
        self._agent = self._create_agent()

    def _llm_call(self, state: MessagesState) -> dict:
        """Invoke the LLM with the current messages.

        Args:
            state: Current state containing messages and LLM call count.

        Returns:
            Updated state with new message and incremented LLM call count.
        """
        return {
            "messages": self._llm.invoke(state["messages"][-1].content)
            + state["messages"],
            "llm_calls": state.get("llm_calls", 0) + 1,
        }

    def _tool_node(self, state: MessagesState) -> dict:
        """Performs the tool call.

        Args:
            state: Current state containing messages and tool call count.

        Returns:
            Updated state with tool messages and incremented tool call count.
        """
        result: list[ToolMessage] = []
        tool_calls: int = 0
        message: AnyMessage = state["messages"][-1]
        if isinstance(message, AIMessage):
            for tool_call in message.tool_calls:
                tool: BaseTool = self._tools_by_name[tool_call["name"]]
                observation: str | list[str | dict] = tool.invoke(tool_call["args"])
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
        agent_builder.add_node("llm_call", self._llm_call)
        agent_builder.add_node("tool_node", self._tool_node)
        agent_builder.add_edge(START, "llm_call")
        agent_builder.add_conditional_edges(
            "llm_call", self._should_continue, ["tool_node", END]
        )
        agent_builder.add_edge("tool_node", "llm_call")
        agent: CompiledStateGraph[MessagesState, None, MessagesState, MessagesState] = (
            agent_builder.compile()
        )
        return agent

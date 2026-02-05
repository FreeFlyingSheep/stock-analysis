"""Tests for chat agent graph."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from langchain.messages import AIMessage, HumanMessage
from langgraph.graph import END

from stock_analysis.agent.graph import ChatAgent
from stock_analysis.agent.model import LLM, Embeddings

if TYPE_CHECKING:
    from langchain.messages import AnyMessage
    from langchain_community.chat_models.fake import FakeListChatModel
    from langchain_community.embeddings import FakeEmbeddings
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    from stock_analysis.agent.graph import MessagesState


@pytest_asyncio.fixture
async def chat_agent(
    postgres_checkpointer: AsyncPostgresSaver,
    fake_chat: FakeListChatModel,
    fake_embeddings: FakeEmbeddings,
) -> ChatAgent:
    llm = LLM(llm=fake_chat)
    embeddings = Embeddings(embeddings=fake_embeddings)
    prompts_dir: Path = Path(__file__).parents[3] / "configs" / "prompts"
    return ChatAgent(
        checkpointer=postgres_checkpointer,
        prompts_dir=prompts_dir,
        llm=llm,
        embeddings=embeddings,
    )


@pytest.mark.asyncio
async def test_trim_messages(chat_agent: ChatAgent) -> None:
    length: int = 30 + 1
    messages: list[AnyMessage] = [HumanMessage(content=f"Test {i}") for i in range(40)]
    state: MessagesState = {"messages": messages}
    result: dict | None = chat_agent._trim_messages(state)
    assert result is not None
    assert "messages" in result
    assert len(result["messages"]) == length


@pytest.mark.asyncio
async def test_should_continue(chat_agent: ChatAgent) -> None:
    ai_message = AIMessage(
        content="Test response with tool call",
        tool_calls=[{"name": "test_tool", "args": {}, "id": "1"}],
    )
    state: MessagesState = {"messages": [ai_message]}
    result: str = chat_agent._should_continue(state)
    assert result == "tool_node"

    ai_message = AIMessage(content="Test response without tool calls")
    state = {"messages": [ai_message]}
    result = chat_agent._should_continue(state)
    assert result == END


@pytest.mark.asyncio
async def test_load_prompt(chat_agent: ChatAgent) -> None:
    prompt1: str = chat_agent._load_prompt("chat", "zh-CN")
    assert isinstance(prompt1, str)
    assert len(prompt1) > 0

    prompt2: str = chat_agent._load_prompt("chat", "en-US")
    assert prompt1 == prompt2

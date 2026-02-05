"""Tests for LLM and Embeddings wrappers."""

from typing import TYPE_CHECKING

import pytest

from stock_analysis.agent.model import LLM, Embeddings

if TYPE_CHECKING:
    from langchain.messages import AIMessage
    from langchain_community.chat_models.fake import FakeListChatModel
    from langchain_community.embeddings.fake import FakeEmbeddings


@pytest.mark.asyncio
async def test_llm(fake_chat: FakeListChatModel) -> None:
    llm = LLM(llm=fake_chat)
    result: AIMessage = llm.invoke("Query 1")
    assert result.content == fake_chat.responses[0]

    result = await llm.ainvoke("Query 2")
    assert result.content == fake_chat.responses[1]


@pytest.mark.asyncio
async def test_embeddings(fake_embeddings: FakeEmbeddings) -> None:
    embeddings = Embeddings(embeddings=fake_embeddings)
    result: list[float] = embeddings.query("Query 1")
    assert len(result) == fake_embeddings.size

    result = await embeddings.aquery("Query 2")
    assert len(result) == fake_embeddings.size

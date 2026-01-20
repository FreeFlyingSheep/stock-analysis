from typing import TYPE_CHECKING

import pytest

from stock_analysis.agent.model import LLM, Embeddings
from stock_analysis.settings import get_settings

if TYPE_CHECKING:
    from langchain.messages import AIMessage


pytestmark: pytest.MarkDecorator = pytest.mark.skipif(
    not get_settings().use_llm, reason="Requires LLM configuration"
)


def test_llm_models() -> None:
    llm: LLM = LLM()
    response: AIMessage = llm.invoke("Hello!")
    assert len(response.content) > 0

    embeddings: Embeddings = Embeddings()
    vector: list[float] = embeddings.query("Hello!")
    assert len(vector) > 0


@pytest.mark.asyncio
async def test_llm_models_async() -> None:
    llm: LLM = LLM()
    response: AIMessage = await llm.ainvoke("Hello!")
    assert len(response.content) > 0

    embeddings: Embeddings = Embeddings()
    vector: list[float] = await embeddings.aquery("Hello!")
    assert len(vector) > 0

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest_asyncio

from stock_analysis.agent.llm import Embeddings
from stock_analysis.agent.retriever import Retriever
from stock_analysis.models.report import ReportChunk

if TYPE_CHECKING:
    from langchain_community.embeddings import FakeEmbeddings
    from sqlalchemy.ext.asyncio import AsyncSession

    from stock_analysis.models.stock import Stock


@pytest_asyncio.fixture
async def retriever(
    async_session: AsyncSession,
    fake_embeddings: FakeEmbeddings,
) -> Retriever:
    return Retriever(
        db=async_session, embeddings=Embeddings(embeddings=fake_embeddings)
    )


@pytest_asyncio.fixture
async def seed_report_chunks(
    async_session: AsyncSession,
    seed_stocks: list[Stock],
    fake_embeddings: FakeEmbeddings,
) -> list[ReportChunk]:
    stock: Stock = seed_stocks[0]
    embedding: list[float] = fake_embeddings.embed_query("dummy")
    chunks: list[ReportChunk] = []
    for i in range(3):
        chunk = ReportChunk(
            stock_id=stock.id,
            fiscal_year=2025,
            report_type="annual",
            content_type="application/pdf",
            doc_id=f"test_doc_{i}",
            doc_version="v1.0.0",
            chunk_no=i,
            content=f"This is test chunk number {i} about financial performance.",
            embedding=embedding,
            updated_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
        )
        chunks.append(chunk)
    async_session.add_all(chunks)
    await async_session.flush()
    return chunks


async def test_retriever(
    retriever: Retriever,
    seed_report_chunks: list[ReportChunk],
) -> None:
    stock_id: int = seed_report_chunks[0].stock_id
    query: str = "financial performance"

    result: str = await retriever.retrieve_semantic(
        query=query, limit=5, stock_id=stock_id, fiscal_year=2025, report_type="annual"
    )
    assert "test chunk number" in result

    no_result: str = await retriever.retrieve_semantic(
        query=query, limit=5, stock_id=stock_id, fiscal_year=9999
    )
    assert no_result == "No relevant report data found."

    result = await retriever.retrieve_bm25(
        query=query, limit=5, stock_id=stock_id, fiscal_year=2025, report_type="annual"
    )
    assert "test chunk number" in result

    result = await retriever.retrieve_hybrid(
        query=query, limit=5, stock_id=stock_id, fiscal_year=2025, report_type="annual"
    )
    assert "test chunk number" in result

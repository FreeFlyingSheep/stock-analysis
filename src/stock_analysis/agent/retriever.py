"""Retriever for stock analysis agent."""

from typing import TYPE_CHECKING

from stock_analysis.agent.model import Embeddings
from stock_analysis.services.report import ReportService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from stock_analysis.models.report import ReportChunk


class Retriever:
    """Retrieves relevant report chunks for a natural-language query.

    Attributes:
        _embeddings: Embedding model wrapper.
        _report_service: Service for querying report chunks.
    """

    _embeddings: Embeddings
    _report_service: ReportService

    def __init__(
        self,
        db: AsyncSession,
        embeddings: Embeddings | None = None,
    ) -> None:
        """Initialize the retriever.

        Args:
            db: Async database session.
            embeddings: Optional embeddings wrapper.
        """
        self._report_service = ReportService(db_session=db)
        self._embeddings = embeddings or Embeddings()

    def _format_chunks(self, chunks: list[ReportChunk]) -> str:
        """Format a list of report chunks into a readable string.

        Args:
            chunks: Report chunks to format.

        Returns:
            Formatted string, or a fallback message if empty.
        """
        if not chunks:
            return "No relevant report data found."

        return "\n\n".join(
            f"[{idx}] doc_id={chunk.doc_id} chunk_no={chunk.chunk_no}\n{chunk.content}"
            for idx, chunk in enumerate(chunks, start=1)
        )

    async def retrieve_semantic(  # noqa: PLR0913
        self,
        query: str,
        limit: int = 5,
        doc_id: str | None = None,
        stock_id: int | None = None,
        fiscal_year: int | None = None,
        report_type: str | None = None,
    ) -> str:
        """Retrieve relevant report chunks using vector similarity only.

        Args:
            query: Natural-language query string.
            limit: Maximum number of chunks to return.
            doc_id: Optional document ID filter.
            stock_id: Optional stock ID filter.
            fiscal_year: Optional fiscal year filter.
            report_type: Optional report type filter.

        Returns:
            A formatted string containing the retrieved chunks.
        """
        query_embedding: list[float] = await self._embeddings.aquery(query)
        chunks: list[ReportChunk] = await self._report_service.search_semantic(
            query_embedding=query_embedding,
            limit=limit,
            doc_id=doc_id,
            stock_id=stock_id,
            fiscal_year=fiscal_year,
            report_type=report_type,
        )
        return self._format_chunks(chunks)

    async def retrieve_bm25(  # noqa: PLR0913
        self,
        query: str,
        limit: int = 5,
        doc_id: str | None = None,
        stock_id: int | None = None,
        fiscal_year: int | None = None,
        report_type: str | None = None,
    ) -> str:
        """Retrieve relevant report chunks for a query using BM25 keyword search.

        Args:
            query: Natural-language query string.
            limit: Maximum number of chunks to return.
            doc_id: Optional document ID filter.
            stock_id: Optional stock ID filter.
            fiscal_year: Optional fiscal year filter.
            report_type: Optional report type filter.

        Returns:
            A formatted string containing the retrieved chunks.
        """
        chunks: list[ReportChunk] = await self._report_service.search_bm25(
            query_str=query,
            limit=limit,
            doc_id=doc_id,
            stock_id=stock_id,
            fiscal_year=fiscal_year,
            report_type=report_type,
        )
        return self._format_chunks(chunks)

    async def retrieve_hybrid(  # noqa: PLR0913
        self,
        query: str,
        limit: int = 5,
        doc_id: str | None = None,
        stock_id: int | None = None,
        fiscal_year: int | None = None,
        report_type: str | None = None,
        semantic_top_n: int = 40,
        bm25_top_n: int = 40,
        rrf_k: int = 60,
    ) -> str:
        """Retrieve relevant report chunks using hybrid search.

        Args:
            query: Natural-language query string.
            limit: Maximum number of chunks to return.
            doc_id: Optional document ID filter.
            stock_id: Optional stock ID filter.
            fiscal_year: Optional fiscal year filter.
            report_type: Optional report type filter.
            semantic_top_n: Number of top semantic results to consider for fusion.
            bm25_top_n: Number of top BM25 results to consider for fusion.
            rrf_k: Parameter to control influence of rank positions in fusion.

        Returns:
            A formatted string containing the retrieved chunks.
        """
        query_embedding: list[float] = await self._embeddings.aquery(query)
        chunks: list[ReportChunk] = await self._report_service.search_hybrid(
            query_embedding=query_embedding,
            query_str=query,
            limit=limit,
            doc_id=doc_id,
            stock_id=stock_id,
            fiscal_year=fiscal_year,
            report_type=report_type,
            semantic_top_n=semantic_top_n,
            bm25_top_n=bm25_top_n,
            rrf_k=rrf_k,
        )
        return self._format_chunks(chunks)

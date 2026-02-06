"""Vector database management service."""

from typing import TYPE_CHECKING

from sqlalchemy import select

from stock_analysis.models.report import ReportChunk

if TYPE_CHECKING:
    from sqlalchemy import Result, Select
    from sqlalchemy.ext.asyncio import AsyncSession


class ReportService:
    """Service for managing financial reports."""

    db: AsyncSession
    """Database session for all operations."""

    def __init__(self, db_session: AsyncSession) -> None:
        """Initialize the ReportService with a database session.

        Args:
            db_session: AsyncSession instance for database operations.
        """
        self.db: AsyncSession = db_session

    async def search_semantic(  # noqa: PLR0913
        self,
        query_embedding: list[float],
        limit: int,
        doc_id: str | None = None,
        stock_id: int | None = None,
        fiscal_year: int | None = None,
        report_type: str | None = None,
    ) -> list[ReportChunk]:
        """Search for report chunks by vector similarity.

        Args:
            query_embedding: The embedding vector to search with.
            limit: The number of top results to return.
            doc_id: Optional document ID to filter by.
            stock_id: Optional stock ID to filter by.
            fiscal_year: Optional fiscal year to filter by.
            report_type: Optional report type to filter by.

        Returns:
            A list of ReportChunk instances matching the search criteria.
        """
        query: Select = (
            select(ReportChunk)
            .order_by(ReportChunk.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )

        if doc_id:
            query = query.where(ReportChunk.doc_id == doc_id)
        if stock_id:
            query = query.where(ReportChunk.stock_id == stock_id)
        if fiscal_year:
            query = query.where(ReportChunk.fiscal_year == fiscal_year)
        if report_type:
            query = query.where(ReportChunk.report_type == report_type)

        result: Result[tuple[ReportChunk]] = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_bm25(  # noqa: PLR0913
        self,
        query_str: str,
        limit: int,
        doc_id: str | None = None,
        stock_id: int | None = None,
        fiscal_year: int | None = None,
        report_type: str | None = None,
    ) -> list[ReportChunk]:
        """Search for report chunks using BM25 keyword matching.

        Args:
            query_str: The input query string to search with.
            limit: The number of top results to return.
            doc_id: Optional document ID to filter by.
            stock_id: Optional stock ID to filter by.
            fiscal_year: Optional fiscal year to filter by.
            report_type: Optional report type to filter by.

        Returns:
            A list of ReportChunk instances matching the search criteria.
        """
        query: Select = (
            select(ReportChunk)
            .where(ReportChunk.content.op("<@>")(query_str))
            .limit(limit)
        )

        if doc_id:
            query = query.where(ReportChunk.doc_id == doc_id)
        if stock_id:
            query = query.where(ReportChunk.stock_id == stock_id)
        if fiscal_year:
            query = query.where(ReportChunk.fiscal_year == fiscal_year)
        if report_type:
            query = query.where(ReportChunk.report_type == report_type)

        result: Result[tuple[ReportChunk]] = await self.db.execute(query)
        return list(result.scalars().all())

    def _rrf_fuse(
        self,
        ranked_lists: list[list[ReportChunk]],
        limit: int,
        rrf_k: int = 60,
    ) -> list[ReportChunk]:
        """Fuse multiple ranked lists using Reciprocal Rank Fusion (RRF).

        Args:
            ranked_lists: A list of ranked lists of ReportChunk instances.
            limit: The number of top results to return after fusion.
            rrf_k: The RRF parameter to control the influence of rank positions.

        Returns:
            Fused list of report chunks ordered by RRF score.
        """
        score_by_id: dict[str, float] = {}
        obj_by_id: dict[str, ReportChunk] = {}

        for ranked in ranked_lists:
            for rank, chunk in enumerate(ranked, start=1):
                key = str(chunk.id)
                obj_by_id[key] = chunk
                score_by_id[key] = score_by_id.get(key, 0.0) + 1.0 / (rrf_k + rank)

        sorted_ids: list[str] = sorted(
            score_by_id.keys(), key=lambda k: score_by_id[k], reverse=True
        )
        return [obj_by_id[k] for k in sorted_ids[:limit]]

    async def search_hybrid(  # noqa: PLR0913
        self,
        query_embedding: list[float],
        query_str: str,
        limit: int,
        doc_id: str | None = None,
        stock_id: int | None = None,
        fiscal_year: int | None = None,
        report_type: str | None = None,
        semantic_top_n: int = 40,
        bm25_top_n: int = 40,
        rrf_k: int = 60,
    ) -> list[ReportChunk]:
        """Search for report chunks using a hybrid of vector similarity and BM25.

        Args:
            query_embedding: The embedding vector to search with.
            query_str: The input query string to search with.
            limit: The number of top results to return.
            doc_id: Optional document ID to filter by.
            stock_id: Optional stock ID to filter by.
            fiscal_year: Optional fiscal year to filter by.
            report_type: Optional report type to filter by.
            semantic_top_n: The number of top results to retrieve from semantic search.
            bm25_top_n: The number of top results to retrieve from BM25 search.
            rrf_k: The parameter to control the influence of rank positions in fusion.

        Returns:
            A list of ReportChunk instances matching the search criteria.
        """
        semantic_hits: list[ReportChunk] = await self.search_semantic(
            query_embedding=query_embedding,
            limit=semantic_top_n,
            doc_id=doc_id,
            stock_id=stock_id,
            fiscal_year=fiscal_year,
            report_type=report_type,
        )
        bm25_hits: list[ReportChunk] = await self.search_bm25(
            query_str=query_str,
            limit=bm25_top_n,
            doc_id=doc_id,
            stock_id=stock_id,
            fiscal_year=fiscal_year,
            report_type=report_type,
        )
        return self._rrf_fuse(
            ranked_lists=[semantic_hits, bm25_hits],
            limit=limit,
            rrf_k=rrf_k,
        )

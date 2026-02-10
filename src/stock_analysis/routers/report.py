"""Financial reports router definitions."""

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from stock_analysis.agent.graph import ChatAgent  # noqa: TC001
from stock_analysis.agent.retriever import Retriever
from stock_analysis.schemas.report import (
    ReportRetrieverBody,  # noqa: TC001
    ReportRetrieverResponse,
)
from stock_analysis.services.agent import get_agent
from stock_analysis.services.database import get_db
from stock_analysis.services.stock import StockService

if TYPE_CHECKING:
    from stock_analysis.models.stock import Stock

router = APIRouter()


@router.post("/reports/retrieve")
async def retrieve_reports(
    body: ReportRetrieverBody,
    db: Annotated[AsyncSession, Depends(get_db)],
    agent: Annotated[ChatAgent, Depends(get_agent)],
) -> ReportRetrieverResponse:
    """Endpoint to retrieve financial reports.

    Args:
        body: Request body containing query and optional filters.
        db: Database session dependency.
        agent: Chat agent dependency for access to embeddings.

    Returns:
        A string containing the retrieved financial reports.
    """
    stock_service = StockService(db)
    stock: Stock | None = None
    if body.stock_code:
        stock = await stock_service.get_stock_by_code(body.stock_code)

    retriever = Retriever(db, agent.get_embeddings())
    data: str = await retriever.retrieve_hybrid(
        query=body.query,
        limit=body.limit,
        doc_id=body.doc_id,
        stock_id=stock.id if stock else None,
        fiscal_year=body.fiscal_year,
        report_type=body.report_type,
        semantic_top_n=body.semantic_top_n,
        bm25_top_n=body.bm25_top_n,
        rrf_k=body.rrf_k,
    )
    return ReportRetrieverResponse(data=data)

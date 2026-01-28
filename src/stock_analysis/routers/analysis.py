"""Score router definitions."""

from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,  # noqa: TC002
    Response,  # noqa: TC002
)
from pgqueuer import PgQueuer  # noqa: TC002
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from stock_analysis.schemas.analysis import (
    AnalysisApiResponse,
    AnalysisDetailApiResponse,
    AnalysisOut,
    AnalysisPage,
)
from stock_analysis.schemas.api import JobPayload
from stock_analysis.services.database import get_db
from stock_analysis.services.pgqueuer import get_pgqueuer
from stock_analysis.services.stock import StockService

if TYPE_CHECKING:
    from pgqueuer.queries import Queries

    from stock_analysis.models.analysis import Analysis
    from stock_analysis.models.stock import Stock


router = APIRouter()


@router.get("/analysis", operation_id="get_analysis")
async def get_analysis(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> AnalysisApiResponse:
    """Display paginated stock analysis results.

    Retrieves computed analysis scores and metrics for stocks with pagination.

    Args:
        db: Database session for data queries.
        page: Page number (1-indexed, defaults to 1, minimum 1).
        size: Items per page (defaults to 50, range 1-200).

    Returns:
        AnalysisApiResponse with paginated analysis results.
    """
    stock_service = StockService(db)

    offset: int = (page - 1) * size
    analysis: list[Analysis] = await stock_service.get_analysis(
        limit=size, offset=offset
    )
    total_count: int = await stock_service.count_analysis()
    total_pages: int = (total_count + size - 1) // size

    return AnalysisApiResponse(
        data=AnalysisPage(
            total=total_pages,
            page_num=page,
            page_size=size,
            data=[AnalysisOut.model_validate(a) for a in analysis],
        ),
    )


@router.get("/analysis/{stock_code}", operation_id="get_analysis_details")
async def get_analysis_details(
    response: Response,
    request: Request,
    stock_code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AnalysisDetailApiResponse:
    """Get analysis details for a specific stock.

    Args:
        response: The HTTP response object.
        request: FastAPI request object for accessing app state.
        stock_code: The stock code to retrieve analysis for.
        db: Database session for data queries.

    Returns:
        Analysis results for the specified stock.

    Raises:
        HTTPException: If the stock with the given code is not found.
    """
    stock_service = StockService(db)

    stock: Stock | None = await stock_service.get_stock_by_code(stock_code)
    if not stock:
        msg: str = f"Stock with code {stock_code} not found."
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=msg)

    analysis: list[Analysis] = await stock_service.get_analysis_by_stock_id(stock.id)
    response_model = AnalysisDetailApiResponse(
        data=[AnalysisOut.model_validate(a) for a in analysis],
    )
    if analysis:
        return response_model

    pgq: PgQueuer = await get_pgqueuer(request)
    queries: Queries = pgq.qm.queries
    payload: JobPayload = JobPayload(stock_code=stock_code)
    await queries.enqueue(
        "analyze_stock_data",
        payload.model_dump_json().encode(),
        priority=5,
    )

    response.status_code = HTTPStatus.ACCEPTED
    return response_model

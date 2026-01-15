"""Stock router definitions."""

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
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from stock_analysis.schemas.api import (
    CNInfoAPIResponseOut,
    JobPayload,
    YahooFinanceAPIResponseOut,
)
from stock_analysis.schemas.stock import (
    StockApiResponse,
    StockDetailApiResponse,
    StockListData,
    StockOut,
    StockPage,
)
from stock_analysis.services.database import get_db
from stock_analysis.services.stock import StockService

if TYPE_CHECKING:
    from pgqueuer import PgQueuer
    from pgqueuer.queries import Queries

    from stock_analysis.models.cninfo import CNInfoAPIResponse
    from stock_analysis.models.stock import Stock
    from stock_analysis.models.yahoo import YahooFinanceAPIResponse

router = APIRouter()


@router.get("/stocks")
async def get_stocks(
    db: Annotated[AsyncSession, Depends(get_db)],
    classification: str | None = None,
    industry: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> StockApiResponse:
    """Display paginated stock list with filtering options.

    Retrieves stocks with optional filtering by classification or industry,
    along with available filter values for the frontend.

    Args:
        db: Database session for data queries.
        classification: Optional filter by classification category.
        industry: Optional filter by industry sector.
        page: Page number (1-indexed, defaults to 1, minimum 1).
        size: Items per page (defaults to 50, range 1-200).

    Returns:
        StockApiResponse with paginated stocks and available filter options.
    """
    stock_service = StockService(db)

    classifications: list[str] = await stock_service.get_classifications()
    industries: list[str] = await stock_service.get_industries(
        classification=classification
    )

    offset: int = (page - 1) * size
    stocks: list[Stock] = await stock_service.get_stocks(
        classification=classification,
        industry=industry,
        limit=size,
        offset=offset,
    )
    total_count: int = await stock_service.count_stocks(
        classification=classification,
        industry=industry,
    )
    total_pages: int = (total_count + size - 1) // size

    return StockApiResponse(
        data=StockListData(
            industries=industries,
            classifications=classifications,
            stock_page=StockPage(
                total=total_pages,
                page_num=page,
                page_size=size,
                data=[StockOut.model_validate(stock) for stock in stocks],
            ),
        ),
    )


@router.get("/stocks/{stock_code}")
async def get_stock_details(
    response: Response,
    request: Request,
    stock_code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StockDetailApiResponse:
    """Get detailed information and API data for a specific stock.

    Retrieves stock information along with CNInfo and Yahoo Finance API
    responses. If data is not cached, queues crawl jobs and returns empty data.

    Args:
        response: The HTTP response object.
        request: FastAPI request object for accessing app state.
        stock_code: The stock code to retrieve details for.
        db: Database session for data queries.

    Returns:
        JSONResponse with stock details and API response data.

    Raises:
        HTTPException: 404 if stock with given code not found.
        HTTPException: 500 if job queue is not initialized.
    """
    stock_service = StockService(db)

    stock: Stock | None = await stock_service.get_stock_by_code(stock_code)
    if not stock:
        msg: str = f"Stock with code {stock_code} not found."
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=msg)

    cninfo_responses: list[
        CNInfoAPIResponse
    ] = await stock_service.get_cninfo_api_responses_by_stock_id(stock.id)
    cninfo_api_responses: list[CNInfoAPIResponseOut] = [
        CNInfoAPIResponseOut.model_validate(response) for response in cninfo_responses
    ]
    yahoo_responses: list[
        YahooFinanceAPIResponse
    ] = await stock_service.get_yahoo_finance_api_responses_by_stock_id(stock.id)
    yahoo_api_responses: list[YahooFinanceAPIResponseOut] = [
        YahooFinanceAPIResponseOut.model_validate(response)
        for response in yahoo_responses
    ]
    response_model = StockDetailApiResponse(
        cninfo_data=cninfo_api_responses, yahoo_data=yahoo_api_responses
    )
    if cninfo_responses and yahoo_responses:
        return response_model

    if not hasattr(request.app.state, "pgq") or request.app.state.pgq is None:
        msg = "Job queue is not initialized."
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg)

    pgq: PgQueuer = request.app.state.pgq
    queries: Queries = pgq.qm.queries
    payload: JobPayload = JobPayload(stock_code=stock_code)
    await queries.enqueue(
        "crawl_stock_data",
        payload.model_dump_json().encode(),
        priority=5,
    )

    response.status_code = HTTPStatus.ACCEPTED
    return response_model

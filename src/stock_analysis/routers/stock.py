"""Stock router definitions."""

from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,  # noqa: TC002
)
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from stock_analysis.schemas.api import CNInfoAPIResponseOut, CNInfoJobPayload
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

    from stock_analysis.models.api import CNInfoAPIResponse
    from stock_analysis.models.stock import Stock

router = APIRouter()


@router.get("/stocks")
async def get_stocks(
    db: Annotated[AsyncSession, Depends(get_db)],
    classification: str | None = None,
    industry: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> StockApiResponse:
    """Display stock list with filtering and pagination.

    Args:
        db: Database session dependency injection.
        classification: Optional filter by classification category.
        industry: Optional filter by industry sector.
        page: Page number for pagination, must be >= 1. Defaults to 1.
        size: Number of items per page, must be between 1 and 200. Defaults to 50.

    Returns:
        StockApiResponse: Paginated stock list with available filters and data.
    """
    stock_service = StockService(db)

    classifications: list[str] = await stock_service.get_classifications()
    industries: list[str] = await stock_service.get_industries()

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
    request: Request,
    stock_code: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """Get detailed information about a specific stock.

    Args:
        request: The FastAPI request object.
        stock_code: The unique code identifying the stock.
        db: Database session dependency injection.

    Returns:
        StockOut: Detailed information about the specified stock.
    """
    stock_service = StockService(db)
    stock: Stock | None = await stock_service.get_stock_by_code(stock_code)
    if not stock:
        msg: str = f"Stock with code {stock_code} not found."
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=msg)

    responses: list[
        CNInfoAPIResponse
    ] = await stock_service.get_cninfo_api_responses_by_stock_id(stock.id)
    api_responses: list[CNInfoAPIResponseOut] = [
        CNInfoAPIResponseOut.model_validate(response) for response in responses
    ]
    response_model = StockDetailApiResponse(data=api_responses)
    data: dict[str, Any] = jsonable_encoder(response_model)
    if responses:
        return JSONResponse(
            content=data,
            status_code=HTTPStatus.OK,
        )

    if not hasattr(request.app.state, "pgq") or request.app.state.pgq is None:
        msg = "Job queue is not initialized."
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=msg)

    pgq: PgQueuer = request.app.state.pgq
    queries: Queries = pgq.qm.queries
    payload: CNInfoJobPayload = CNInfoJobPayload(stock_code=stock_code)
    await queries.enqueue(
        "crawl_stock_data",
        payload.model_dump_json().encode(),
        priority=5,
    )

    return JSONResponse(content=data, status_code=HTTPStatus.ACCEPTED)

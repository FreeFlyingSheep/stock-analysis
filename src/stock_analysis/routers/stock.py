"""Stock router definitions."""

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from stock_analysis.schemas.stock import (
    StockApiResponse,
    StockListData,
    StockOut,
    StockPage,
)
from stock_analysis.services.database import get_db
from stock_analysis.services.stock import StockService

if TYPE_CHECKING:
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

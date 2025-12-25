"""Stock schema definitions."""

from datetime import datetime

from stock_analysis.schemas.api import CNInfoAPIResponseOut
from stock_analysis.schemas.base import BaseSchema


class BaseStock(BaseSchema):
    """Base stock schema.

    Contains the minimal required fields for stock identification.

    Attributes:
        stock_code: Unique stock identifier code.
        company_name: Name of the company.
    """

    stock_code: str
    company_name: str


class StockIn(BaseStock):
    """Stock information input schema.

    Schema for creating or updating stock records.

    Attributes:
        classification: Stock classification category.
        industry: Industry sector of the stock.
    """

    classification: str
    industry: str


class StockOut(StockIn):
    """Stock output schema.

    Schema for returning stock data from the API, including timestamps.

    Attributes:
        created_at: Timestamp when the record was created.
        updated_at: Timestamp when the record was last updated.
    """

    created_at: datetime
    updated_at: datetime


class StockPage(BaseSchema):
    """Paginated stock response schema.

    Contains pagination metadata and stock data for a single page.

    Attributes:
        total: Total number of pages available.
        page_num: Current page number.
        page_size: Number of items per page.
        data: List of stock records for the current page.
    """

    total: int
    page_num: int
    page_size: int
    data: list[StockOut]


class StockListData(BaseSchema):
    """Stock list data schema.

    Container for stock list response including available filters and paginated data.

    Attributes:
        industries: List of all available industry names.
        classifications: List of all available classification names.
        stock_page: Paginated stock data.
    """

    industries: list[str]
    classifications: list[str]
    stock_page: StockPage


class StockApiResponse(BaseSchema):
    """Stock API response schema.

    Top-level API response wrapper for stock list endpoints.

    Attributes:
        data: Stock list data including filters and pagination.
    """

    data: StockListData


class StockDetailApiResponse(BaseSchema):
    """Stock detail API response schema.

    Top-level API response wrapper for stock detail endpoints.

    Attributes:
        data: Detailed stock information.
    """

    data: list[CNInfoAPIResponseOut]

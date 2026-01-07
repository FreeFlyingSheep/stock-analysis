"""Stock schema definitions."""

from datetime import datetime

from stock_analysis.schemas.api import CNInfoAPIResponseOut, YahooFinanceAPIResponseOut
from stock_analysis.schemas.base import BaseSchema


class BaseStock(BaseSchema):
    """Base schema with required stock identification fields.

    Attributes:
        stock_code: Unique stock identifier code.
        company_name: Name of the company.
    """

    stock_code: str
    company_name: str


class StockIn(BaseStock):
    """Input schema for creating or updating stock records.

    Attributes:
        classification: Stock classification category.
        industry: Industry sector of the stock.
    """

    classification: str
    industry: str


class StockOut(StockIn):
    """Output schema for returning stock data from the API.

    Extends StockIn with timestamp fields.

    Attributes:
        created_at: Timestamp when record was created.
        updated_at: Timestamp when record was last updated.
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
    """Container for stock list response data.

    Includes available filters and paginated stock data.

    Attributes:
        industries: List of all available industry names.
        classifications: List of all available classification names.
        stock_page: Paginated stock data.
    """

    industries: list[str]
    classifications: list[str]
    stock_page: StockPage


class StockApiResponse(BaseSchema):
    """Top-level API response wrapper for stock list endpoints.

    Attributes:
        data: Stock list data including filters and pagination.
    """

    data: StockListData


class StockDetailApiResponse(BaseSchema):
    """Top-level API response wrapper for stock detail endpoints.

    Attributes:
        cninfo_data: Detailed CNInfo API response data.
        yahoo_data: Detailed Yahoo Finance API response data.
    """

    cninfo_data: list[CNInfoAPIResponseOut]
    yahoo_data: list[YahooFinanceAPIResponseOut]

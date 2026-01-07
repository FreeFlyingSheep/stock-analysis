"""Schemas for stock analysis results."""

from datetime import datetime

from stock_analysis.schemas.base import BaseSchema


class BaseAnalysis(BaseSchema):
    """Base schema for stock analysis.

    Attributes:
        stock_id: The ID of the stock analyzed.
        metrics: A dictionary of computed metrics.
        score: Overall score from the analysis.
    """

    stock_id: int
    metrics: dict[str, float]
    score: float


class AnalysisIn(BaseAnalysis):
    """Input schema for stock analysis.

    Attributes:
        filtered: Whether the stock passed the analysis filters.
    """

    filtered: bool


class AnalysisOut(BaseAnalysis):
    """Output schema for stock analysis.

    Attributes:
        created_at: Timestamp when the analysis record was created.
        updated_at: Timestamp when the analysis record was last updated.
    """

    created_at: datetime
    updated_at: datetime


class AnalysisPage(BaseSchema):
    """Paginated analysis response schema.

    Attributes:
        total: Total number of pages available.
        page_num: Current page number.
        page_size: Number of items per page.
        data: List of analysis records for the current page.
    """

    total: int
    page_num: int
    page_size: int
    data: list[AnalysisOut]


class AnalysisApiResponse(BaseSchema):
    """API response schema for analysis results.

    Attributes:
        data: Paginated analysis data.
    """

    data: AnalysisPage


class AnalysisDetailApiResponse(BaseSchema):
    """API response schema for detailed analysis of a specific stock.

    Attributes:
        stock_code: The stock code for which the analysis is provided.
        analysis: List of analysis records for the stock.
    """

    data: list[AnalysisOut]

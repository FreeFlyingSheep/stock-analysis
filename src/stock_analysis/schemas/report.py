"""Schemas for financial reports."""

from datetime import datetime

from stock_analysis.schemas.base import BaseSchema


class ReportChunkIn(BaseSchema):
    """Input schema for creating a report chunk.

    Attributes:
        stock_id: Stock ID associated with the report chunk.
        fiscal_year: Fiscal year of the report.
        report_type: Type of the report (e.g., annual).
        content_type: Mime type of the report content (e.g., application/pdf).
        doc_id: Document ID of the report chunk.
        doc_version: Document version of the report chunk.
        chunk_no: Chunk number for the report.
        content: Text content of the report chunk.
    """

    stock_id: int
    fiscal_year: int
    report_type: str
    content_type: str
    doc_id: str
    doc_version: str
    chunk_no: int
    content: str
    embedding: list[float]


class ReportChunkOut(ReportChunkIn):
    """Output schema for a report chunk, including the ID and embedding.

    Attributes:
        id: Primary key identifier.
        embedding: Vector embedding for the report chunk.
    """

    id: int
    updated_at: datetime
    created_at: datetime

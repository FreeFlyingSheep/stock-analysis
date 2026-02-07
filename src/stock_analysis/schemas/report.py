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


class RawChunk(BaseSchema):
    """Schema for intermediate chunk extracted from PDF parsing.

    Attributes:
        chunk_id: Stable SHA-1 identifier for the chunk.
        doc_id: Document identifier derived from object key and etag.
        source_key: MinIO object key of the source PDF.
        source_version: Version of the source PDF.
        page: One-based page number of the chunk source.
        heading: Section heading associated with the chunk.
        chunk_index: Sequential index of the chunk within the document.
        content: Text content of the chunk.
    """

    chunk_id: str
    doc_id: str
    source_key: str
    source_version: str
    page: int
    heading: str
    chunk_index: int
    content: str

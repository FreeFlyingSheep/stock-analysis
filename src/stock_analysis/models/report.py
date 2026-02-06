"""Financial report models for storage and retrieval."""

from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import VECTOR  # type: ignore[import-untyped]
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stock_analysis.models.base import Base

if TYPE_CHECKING:
    from stock_analysis.models.stock import Stock


EMBEDDING_DIMENSION = 768
"""Embedding dimension for the embeddings model."""


class ReportChunk(Base):
    """Report chunks for financial reports, used for storage and retrieval.

    Attributes:
        id: Primary key identifier.
        stock_id: Foreign key to the associated stock.
        fiscal_year: Fiscal year of the report.
        report_type: Type of the report (e.g., annual, quarterly).
        content_type: Mime type of the report content (e.g., application/pdf).
        title: Title of the report chunk.
        file_url: URL to the original report file.
        chunk_no: Chunk number for the report.
        content: Text content of the report chunk.
        embedding: Vector embedding for the report chunk.
        created_at: Timestamp when the chunk was created.
        updated_at: Timestamp when the chunk was last updated.
    """

    __tablename__: str = "report_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    fiscal_year: Mapped[int] = mapped_column(nullable=False)
    report_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content_type: Mapped[str] = mapped_column(String(32), nullable=False)

    doc_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    doc_version: Mapped[str] = mapped_column(String(100), nullable=False)

    chunk_no: Mapped[int] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        VECTOR(dim=EMBEDDING_DIMENSION), nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    stock: Mapped["Stock"] = relationship(
        back_populates="report_chunks",
    )

"""Stock model definition."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stock_analysis.models.base import Base

if TYPE_CHECKING:
    from stock_analysis.models.analysis import Analysis
    from stock_analysis.models.cninfo import CNInfoAPIResponse
    from stock_analysis.models.report import ReportChunk
    from stock_analysis.models.yahoo import YahooFinanceAPIResponse


class Stock(Base):
    """Stock information database model.

    Represents stock information including company details, classification,
    industry, and timestamps. Maps to the 'stocks' database table.

    Attributes:
        id: Primary key identifier.
        stock_code: Unique stock identifier code (max 10 chars).
        company_name: Name of the company (max 200 chars).
        classification: Stock classification category (max 100 chars).
        industry: Industry sector of the stock (max 100 chars).
        created_at: Timestamp when record was created (timezone-aware UTC).
        updated_at: Timestamp when record was last updated (timezone-aware UTC).
        cninfo_api_responses: Relationship to CNInfo API responses.
        yahoo_finance_api_responses: Relationship to Yahoo Finance API responses.
        analysis: Relationship to analysis records.
        reports: Relationship to report chunks.
    """

    __tablename__: str = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    classification: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    cninfo_api_responses: Mapped[list["CNInfoAPIResponse"]] = relationship(
        back_populates="stock",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    yahoo_finance_api_responses: Mapped[list["YahooFinanceAPIResponse"]] = relationship(
        back_populates="stock",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    analysis: Mapped[list["Analysis"]] = relationship(
        back_populates="stock",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    report_chunks: Mapped[list["ReportChunk"]] = relationship(
        back_populates="stock",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        """Return a string representation of the Stock instance.

        Returns:
            String representation of the Stock instance.
        """
        return (
            f"Stock(id={self.id!r}, "
            f"stock_code={self.stock_code!r},"
            f"company_name={self.company_name!r}, "
            f"classification={self.classification!r},"
            f"industry={self.industry!r}, "
            f"created_at={self.created_at!r},"
            f"updated_at={self.updated_at!r})"
        )

"""Stock model definition."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from stock_analysis.models.base import Base


class Stock(Base):
    """Stock information model.

    This model represents stock information including company details,
    classification, industry, and timestamps.

    Attributes:
        stock_code: Unique stock identifier code.
        company_name: Name of the company.
        classification: Stock classification category.
        industry: Industry sector of the stock.
        created_at: Timestamp when the record was created.
        updated_at: Timestamp when the record was last updated.
    """

    __tablename__: str = "stocks"

    stock_code: Mapped[str] = mapped_column(String(10), primary_key=True)
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

    def __repr__(self) -> str:
        """Get a string representation of the Stock object.

        Returns:
            str: String representation of the Stock instance.
        """
        return (
            f"Stock(stock_code={self.stock_code!r},"
            f"company_name={self.company_name!r}, "
            f"classification={self.classification!r},"
            f"industry={self.industry!r}, "
            f"created_at={self.created_at!r},"
            f"updated_at={self.updated_at!r})"
        )

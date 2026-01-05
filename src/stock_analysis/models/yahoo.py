"""Yahoo Finance API data models for raw data."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stock_analysis.models.base import Base

if TYPE_CHECKING:
    from stock_analysis.models.stock import Stock


class YahooFinanceAPIResponse(Base):
    """Raw API responses from Yahoo Finance endpoints."""

    __tablename__: str = "yahoo_finance_api_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    params: Mapped[dict] = mapped_column(JSONB, nullable=False)
    raw_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    stock: Mapped["Stock"] = relationship(
        back_populates="yahoo_finance_api_responses",
    )

    def __repr__(self) -> str:
        """Get a string representation of the YahooFinanceAPIResponse object."""
        return (
            f"YahooFinanceAPIResponse(params={self.params!r}, "
            f"raw_json={self.raw_json!r}, created_at={self.created_at!r}, "
            f"updated_at={self.updated_at!r})"
        )

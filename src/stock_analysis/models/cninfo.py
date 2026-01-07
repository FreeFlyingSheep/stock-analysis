"""CNInfo API data models for storing raw endpoint responses."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stock_analysis.models.base import Base

if TYPE_CHECKING:
    from stock_analysis.models.stock import Stock


class CNInfoAPIResponse(Base):
    """Raw API response data from CNInfo endpoints.

    Stores raw JSON responses and metadata from CNInfo API calls including
    request parameters, response codes, and timestamps.

    Attributes:
        id: Primary key identifier.
        stock_id: Foreign key reference to the stock.
        endpoint: CNInfo endpoint name (e.g., 'balance_sheets', 'income_statement').
        params: Request parameters used for the API call (JSONB format).
        response_code: HTTP response code from the endpoint.
        raw_json: Raw JSON response from the endpoint (JSONB format).
        created_at: Timestamp when record was created (timezone-aware UTC).
        updated_at: Timestamp when record was last updated (timezone-aware UTC).
        stock: Relationship to the associated Stock model.
    """

    __tablename__: str = "cninfo_api_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    endpoint: Mapped[str] = mapped_column(String(100), nullable=False)
    params: Mapped[dict] = mapped_column(JSONB, nullable=False)
    response_code: Mapped[int | None] = mapped_column(Integer, nullable=False)
    raw_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    stock: Mapped["Stock"] = relationship(
        back_populates="cninfo_api_responses",
    )

    def __repr__(self) -> str:
        """Return a string representation of the CNInfoAPIResponse instance.

        Returns:
            String representation containing endpoint, params, response_code,
            raw_json, and timestamp information.
        """
        return (
            f"CNInfoAPIResponse(endpoint={self.endpoint!r}, "
            f"params={self.params!r}, response_code={self.response_code!r}, "
            f"raw_json={self.raw_json!r}, created_at={self.created_at!r}, "
            f"updated_at={self.updated_at!r})"
        )

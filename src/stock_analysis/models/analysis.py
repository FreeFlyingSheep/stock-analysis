"""Stock analysis model definition."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stock_analysis.models.base import Base

if TYPE_CHECKING:
    from stock_analysis.models.stock import Stock


class Analysis(Base):
    """Stock analysis result model.

    This model represents the results of stock analysis including
    computed metrics and timestamps.

    Attributes:
        stock_id: The ID of the stock analyzed.
        metrics: A JSON string of computed metrics.
        score: Overall score from the analysis.
        filtered: A boolean indicating if the stock passed filtering criteria.
        created_at: Timestamp when the record was created.
        updated_at: Timestamp when the record was last updated.
    """

    __tablename__: str = "analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metrics: Mapped[str] = mapped_column(JSONB, nullable=False)
    score: Mapped[float] = mapped_column(nullable=False)
    filtered: Mapped[bool] = mapped_column(nullable=False)

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

    stock: Mapped["Stock"] = relationship(
        back_populates="analysis",
    )

    def __repr__(self) -> str:
        """Get a string representation of the Analysis object."""
        return (
            f"Analysis(id={self.id!r}, "
            f"stock_id={self.stock_id!r}, "
            f"score={self.score!r}), "
            f"created_at={self.created_at!r}, "
            f"updated_at={self.updated_at!r})"
        )

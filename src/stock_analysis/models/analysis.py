"""Stock analysis results database models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stock_analysis.models.base import Base

if TYPE_CHECKING:
    from stock_analysis.models.stock import Stock


class Analysis(Base):
    """Stock analysis results database model.

    Stores computed analysis metrics and scores for stocks including
    financial indicators and filtering status.

    Attributes:
        id: Primary key identifier.
        stock_id: Foreign key reference to the stock.
        metrics: Computed metrics as JSON/JSONB object mapping metric names to values.
        score: Overall analysis score calculated from metrics and rules.
        filtered: Boolean indicating if stock passed filter criteria.
        created_at: Timestamp when record was created (timezone-aware UTC).
        updated_at: Timestamp when record was last updated (timezone-aware UTC).
        stock: Relationship to the associated Stock model.
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
        """Return a string representation of the Analysis instance.

        Returns:
            String representation containing id, stock_id, score,
            and timestamp information.
        """
        return (
            f"Analysis(id={self.id!r}, "
            f"stock_id={self.stock_id!r}, "
            f"score={self.score!r}), "
            f"created_at={self.created_at!r}, "
            f"updated_at={self.updated_at!r})"
        )

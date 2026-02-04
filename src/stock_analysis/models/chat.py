"""Stock analysis chat models."""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from stock_analysis.models.base import Base


class ChatThread(Base):
    """Chat thread database model.

    Represents stock information including company details, classification,
    industry, and timestamps. Maps to the 'stocks' database table.

    Attributes:
        id: Primary key identifier.
        thread_id: Unique thread identifier.
        title: Title of the chat thread.
        status: Current status of the chat thread.
        created_at: Timestamp when record was created (timezone-aware UTC).
        updated_at: Timestamp when record was last updated (timezone-aware UTC).
    """

    __tablename__: str = "chat_threads"

    id: Mapped[int] = mapped_column(primary_key=True)
    thread_id: Mapped[str] = mapped_column(nullable=False, unique=True)
    title: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)

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
        """Return a string representation of the Stock instance.

        Returns:
            String representation of the Stock instance.
        """
        return (
            f"ChatThread(id={self.id!r}, "
            f"thread_id={self.thread_id!r},"
            f"title={self.title!r}, "
            f"status={self.status!r},"
            f"created_at={self.created_at!r},"
            f"updated_at={self.updated_at!r})"
        )

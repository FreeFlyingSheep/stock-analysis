"""Add report table.

Revision ID: 403be8a6ccc8
Revises: 31ec239aaf59
Create Date: 2026-02-06 16:44:09.411750

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import VECTOR  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = "403be8a6ccc8"
down_revision: str | Sequence[str] | None = "31ec239aaf59"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "report_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("report_type", sa.String(length=32), nullable=False),
        sa.Column("content_type", sa.String(length=32), nullable=False),
        sa.Column("doc_id", sa.String(length=100), nullable=False),
        sa.Column("doc_version", sa.String(length=100), nullable=False),
        sa.Column("chunk_no", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", VECTOR(dim=768), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("doc_id"),
    )
    op.create_index(
        op.f("ix_report_chunks_stock_id"), "report_chunks", ["stock_id"], unique=False
    )
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_set_updated_at ON report_chunks;
        CREATE TRIGGER trg_set_updated_at
        BEFORE UPDATE ON report_chunks
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
        """,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS trg_set_updated_at ON report_chunks;")
    op.drop_index(op.f("ix_report_chunks_stock_id"), table_name="report_chunks")
    op.drop_table("report_chunks")

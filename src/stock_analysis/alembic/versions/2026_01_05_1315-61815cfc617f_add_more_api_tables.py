"""Add more api tables.

Revision ID: 61815cfc617f
Revises: 0168db90f4d0
Create Date: 2026-01-05 13:15:15.502373

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "61815cfc617f"
down_revision: str | Sequence[str] | None = "0168db90f4d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "yahoo_finance_api_responses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("period", sa.String(length=20), nullable=False),
        sa.Column("interval", sa.String(length=20), nullable=False),
        sa.Column("raw_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["stock_id"], ["stocks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_yahoo_finance_api_responses_stock_id"),
        "yahoo_finance_api_responses",
        ["stock_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_yahoo_finance_api_responses_stock_id"),
        table_name="yahoo_finance_api_responses",
    )
    op.drop_table("yahoo_finance_api_responses")

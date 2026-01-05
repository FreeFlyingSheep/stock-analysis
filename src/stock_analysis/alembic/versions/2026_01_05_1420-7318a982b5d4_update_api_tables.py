"""Update api tables.

Revision ID: 7318a982b5d4
Revises: 61815cfc617f
Create Date: 2026-01-05 14:20:46.221116

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "7318a982b5d4"
down_revision: str | Sequence[str] | None = "61815cfc617f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "yahoo_finance_api_responses",
        sa.Column("params", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.drop_column("yahoo_finance_api_responses", "symbol")
    op.drop_column("yahoo_finance_api_responses", "period")
    op.drop_column("yahoo_finance_api_responses", "interval")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "yahoo_finance_api_responses",
        sa.Column(
            "interval", sa.VARCHAR(length=20), autoincrement=False, nullable=False
        ),
    )
    op.add_column(
        "yahoo_finance_api_responses",
        sa.Column("period", sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    )
    op.add_column(
        "yahoo_finance_api_responses",
        sa.Column("symbol", sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    )
    op.drop_column("yahoo_finance_api_responses", "params")

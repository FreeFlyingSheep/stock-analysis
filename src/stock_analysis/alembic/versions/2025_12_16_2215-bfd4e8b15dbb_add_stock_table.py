"""Add stock table.

Revision ID: bfd4e8b15dbb
Revises:
Create Date: 2025-12-16 22:15:30.437305

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "bfd4e8b15dbb"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """,
    )
    op.create_table(
        "stocks",
        sa.Column("stock_code", sa.String(length=10), nullable=False),
        sa.Column("company_name", sa.String(length=200), nullable=False),
        sa.Column("classification", sa.String(length=100), nullable=False),
        sa.Column("industry", sa.String(length=100), nullable=False),
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
        sa.PrimaryKeyConstraint("stock_code"),
    )
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_set_updated_at ON stocks;
        CREATE TRIGGER trg_set_updated_at
        BEFORE UPDATE ON stocks
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
        """,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS trg_set_updated_at ON stocks;")
    op.drop_table("stocks")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at();")

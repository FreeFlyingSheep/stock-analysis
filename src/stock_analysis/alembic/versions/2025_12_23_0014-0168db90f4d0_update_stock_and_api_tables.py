"""Update stock and api tables.

Revision ID: 0168db90f4d0
Revises: e6532b8d353e
Create Date: 2025-12-23 00:14:23.336899

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = "0168db90f4d0"
down_revision: str | Sequence[str] | None = "e6532b8d353e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "cninfo_api_responses", sa.Column("stock_id", sa.Integer(), nullable=False)
    )
    op.drop_index(
        op.f("ix_cninfo_api_responses_stock_code"), table_name="cninfo_api_responses"
    )
    op.create_index(
        op.f("ix_cninfo_api_responses_stock_id"),
        "cninfo_api_responses",
        ["stock_id"],
        unique=False,
    )
    op.drop_constraint(
        op.f("cninfo_api_responses_stock_code_fkey"),
        "cninfo_api_responses",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "cninfo_api_responses_stock_id_fkey",
        "cninfo_api_responses",
        "stocks",
        ["stock_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_column("cninfo_api_responses", "stock_code")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "cninfo_api_responses",
        sa.Column("stock_code", sa.INTEGER(), autoincrement=False, nullable=False),
    )
    op.drop_constraint(
        "cninfo_api_responses_stock_id_fkey", "cninfo_api_responses", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("cninfo_api_responses_stock_code_fkey"),
        "cninfo_api_responses",
        "stocks",
        ["stock_code"],
        ["id"],
    )
    op.drop_index(
        op.f("ix_cninfo_api_responses_stock_id"), table_name="cninfo_api_responses"
    )
    op.create_index(
        op.f("ix_cninfo_api_responses_stock_code"),
        "cninfo_api_responses",
        ["stock_code"],
        unique=False,
    )
    op.drop_column("cninfo_api_responses", "stock_id")

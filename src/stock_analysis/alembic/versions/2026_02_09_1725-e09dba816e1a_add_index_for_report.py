"""Add index for report.

Revision ID: e09dba816e1a
Revises: c5acef334e07
Create Date: 2026-02-09 17:25:18.855941

"""

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = "e09dba816e1a"
down_revision: str | Sequence[str] | None = "c5acef334e07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "idx_report_chunks_bm25",
        "report_chunks",
        ["content"],
        unique=False,
        postgresql_using="bm25",
        postgresql_with={"text_config": "public.chinese"},
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_report_chunks_bm25", table_name="report_chunks")

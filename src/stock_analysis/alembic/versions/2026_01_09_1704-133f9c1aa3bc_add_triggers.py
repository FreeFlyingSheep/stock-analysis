"""Add triggers.

Revision ID: 133f9c1aa3bc
Revises: 6b97746b3d71
Create Date: 2026-01-09 17:04:37.095853

"""

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = "133f9c1aa3bc"
down_revision: str | Sequence[str] | None = "6b97746b3d71"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_set_updated_at ON yahoo_finance_api_responses;
        CREATE TRIGGER trg_set_updated_at
        BEFORE UPDATE ON yahoo_finance_api_responses
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
        """,
    )
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_set_updated_at ON analysis;
        CREATE TRIGGER trg_set_updated_at
        BEFORE UPDATE ON analysis
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
        """,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DROP TRIGGER IF EXISTS trg_set_updated_at ON yahoo_finance_api_responses;"
    )
    op.execute("DROP TRIGGER IF EXISTS trg_set_updated_at ON analysis;")

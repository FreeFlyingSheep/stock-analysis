"""Update analysis table.

Revision ID: 6b97746b3d71
Revises: ef35841c6a71
Create Date: 2026-01-07 12:10:30.218387

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = "6b97746b3d71"
down_revision: str | Sequence[str] | None = "ef35841c6a71"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("analysis", sa.Column("filtered", sa.Boolean(), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("analysis", "filtered")

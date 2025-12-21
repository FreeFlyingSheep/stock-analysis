"""Add cninfo api responses table.

Revision ID: e6532b8d353e
Revises: bfd4e8b15dbb
Create Date: 2025-12-21 11:23:41.681722

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "e6532b8d353e"
down_revision: str | Sequence[str] | None = "bfd4e8b15dbb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("stocks", sa.Column("id", sa.Integer(), nullable=True))
    op.execute("CREATE SEQUENCE IF NOT EXISTS stocks_id_seq;")
    op.execute("ALTER SEQUENCE stocks_id_seq OWNED BY stocks.id;")
    op.execute(
        "ALTER TABLE stocks ALTER COLUMN id SET DEFAULT nextval('stocks_id_seq');"
    )
    op.execute("UPDATE stocks SET id = DEFAULT WHERE id IS NULL;")
    op.alter_column("stocks", "id", nullable=False)
    op.create_unique_constraint("stocks_stock_code_key", "stocks", ["stock_code"])
    op.execute("ALTER TABLE stocks DROP CONSTRAINT IF EXISTS stocks_pkey;")
    op.create_primary_key("stocks_pkey", "stocks", ["id"])

    op.create_table(
        "cninfo_api_responses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("endpoint", sa.String(length=100), nullable=False),
        sa.Column("stock_code", sa.Integer(), nullable=False),
        sa.Column("params", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("response_code", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(["stock_code"], ["stocks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_cninfo_api_responses_stock_code"),
        "cninfo_api_responses",
        ["stock_code"],
    )
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_set_updated_at ON cninfo_api_responses;
        CREATE TRIGGER trg_set_updated_at
        BEFORE UPDATE ON cninfo_api_responses
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
        """,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TRIGGER IF EXISTS trg_set_updated_at ON cninfo_api_responses;")
    op.drop_index(
        op.f("ix_cninfo_api_responses_stock_code"), table_name="cninfo_api_responses"
    )
    op.drop_table("cninfo_api_responses")

    op.execute("ALTER TABLE stocks DROP CONSTRAINT IF EXISTS stocks_pkey;")
    op.create_primary_key("stocks_pkey", "stocks", ["stock_code"])
    op.drop_constraint("stocks_stock_code_key", "stocks", type_="unique")
    op.drop_column("stocks", "id")
    op.execute("DROP SEQUENCE IF EXISTS stocks_id_seq;")

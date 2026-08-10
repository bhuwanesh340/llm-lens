"""create models table

Revision ID: d671f7079cac
Revises: a474e06425a1
Create Date: 2026-08-11 00:25:50.752828

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd671f7079cac'
down_revision: str | None = 'a474e06425a1'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "models",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("provider_id", sa.Uuid(), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("input_price_per_1m", sa.Numeric(18, 8), nullable=True),
        sa.Column("output_price_per_1m", sa.Numeric(18, 8), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["provider_id"], ["providers.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("provider_id", "model_name", name="uq_models_provider_id_model_name"),
    )
    op.create_index("ix_models_provider_id", "models", ["provider_id"])
    op.create_index("ix_models_model_name", "models", ["model_name"])


def downgrade() -> None:
    op.drop_index("ix_models_model_name", table_name="models")
    op.drop_index("ix_models_provider_id", table_name="models")
    op.drop_table("models")

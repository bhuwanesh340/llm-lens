"""create applications table

Revision ID: fdff25b92bf5
Revises: d671f7079cac
Create Date: 2026-08-11 00:25:52.619350

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'fdff25b92bf5'
down_revision: str | None = 'd671f7079cac'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("environment", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("slug", name="uq_applications_slug"),
    )
    op.create_index("ix_applications_slug", "applications", ["slug"])


def downgrade() -> None:
    op.drop_index("ix_applications_slug", table_name="applications")
    op.drop_table("applications")

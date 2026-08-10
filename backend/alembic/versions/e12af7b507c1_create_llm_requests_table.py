"""create llm_requests table

Revision ID: e12af7b507c1
Revises: 501668be4dea
Create Date: 2026-08-11 00:25:57.038731

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e12af7b507c1'
down_revision: str | None = '501668be4dea'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "llm_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("request_id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("input_cost", sa.Numeric(18, 8), nullable=True),
        sa.Column("output_cost", sa.Numeric(18, 8), nullable=True),
        sa.Column("total_cost", sa.Numeric(18, 8), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ttft_ms", sa.Integer(), nullable=True),
        sa.Column("application_id", sa.Uuid(), nullable=True),
        sa.Column("environment", sa.String(length=64), nullable=True),
        sa.Column("api_key_id", sa.Uuid(), nullable=True),
        sa.Column("error_type", sa.String(length=32), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.ForeignKeyConstraint(["provider"], ["providers.name"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["application_id"], ["applications.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["api_key_id"], ["api_keys.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("request_id", name="uq_llm_requests_request_id"),
        sa.CheckConstraint("status IN ('success', 'error')", name="ck_llm_requests_status"),
        sa.CheckConstraint("input_tokens >= 0", name="ck_llm_requests_input_tokens_nonneg"),
        sa.CheckConstraint("output_tokens >= 0", name="ck_llm_requests_output_tokens_nonneg"),
        sa.CheckConstraint("total_tokens >= 0", name="ck_llm_requests_total_tokens_nonneg"),
        sa.CheckConstraint("latency_ms >= 0", name="ck_llm_requests_latency_ms_nonneg"),
    )
    op.create_index("ix_llm_requests_created_at", "llm_requests", ["created_at"])
    op.create_index("ix_llm_requests_provider", "llm_requests", ["provider"])
    op.create_index("ix_llm_requests_model", "llm_requests", ["model"])
    op.create_index("ix_llm_requests_application_id", "llm_requests", ["application_id"])
    op.create_index("ix_llm_requests_status", "llm_requests", ["status"])


def downgrade() -> None:
    op.drop_index("ix_llm_requests_status", table_name="llm_requests")
    op.drop_index("ix_llm_requests_application_id", table_name="llm_requests")
    op.drop_index("ix_llm_requests_model", table_name="llm_requests")
    op.drop_index("ix_llm_requests_provider", table_name="llm_requests")
    op.drop_index("ix_llm_requests_created_at", table_name="llm_requests")
    op.drop_table("llm_requests")

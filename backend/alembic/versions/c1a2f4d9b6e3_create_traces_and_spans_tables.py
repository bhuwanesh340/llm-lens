"""create traces and spans tables

Revision ID: c1a2f4d9b6e3
Revises: b7c3d9e14f28
Create Date: 2026-08-19 00:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1a2f4d9b6e3"
down_revision: str | None = "b7c3d9e14f28"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TRACE_STATUSES = ("running", "success", "error")
_SPAN_STATUSES = ("running", "success", "error")
_SPAN_KINDS = ("llm", "tool", "retriever", "embedding", "chain", "agent", "custom")


def upgrade() -> None:
    op.create_table(
        "traces",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("environment", sa.String(length=64), nullable=True),
        # Generic JSON (not JSONB) so this table is SQLite-portable from day one.
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.CheckConstraint(f"status IN {_TRACE_STATUSES}", name="ck_traces_status"),
    )
    op.create_index("ix_traces_project_id", "traces", ["project_id"])
    op.create_index("ix_traces_started_at", "traces", ["started_at"])

    op.create_table(
        "spans",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("parent_span_id", sa.String(length=64), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False, server_default="custom"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("input_cost", sa.Numeric(18, 8), nullable=True),
        sa.Column("output_cost", sa.Numeric(18, 8), nullable=True),
        sa.Column("total_cost", sa.Numeric(18, 8), nullable=True),
        sa.Column("input", sa.JSON(), nullable=True),
        sa.Column("output", sa.JSON(), nullable=True),
        sa.Column("error_type", sa.String(length=32), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.ForeignKeyConstraint(["trace_id"], ["traces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_span_id"], ["spans.id"], ondelete="SET NULL"),
        sa.CheckConstraint(f"status IN {_SPAN_STATUSES}", name="ck_spans_status"),
        sa.CheckConstraint(f"kind IN {_SPAN_KINDS}", name="ck_spans_kind"),
    )
    op.create_index("ix_spans_trace_id", "spans", ["trace_id"])
    op.create_index("ix_spans_parent_span_id", "spans", ["parent_span_id"])
    op.create_index("ix_spans_started_at", "spans", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_spans_started_at", table_name="spans")
    op.drop_index("ix_spans_parent_span_id", table_name="spans")
    op.drop_index("ix_spans_trace_id", table_name="spans")
    op.drop_table("spans")
    op.drop_index("ix_traces_started_at", table_name="traces")
    op.drop_index("ix_traces_project_id", table_name="traces")
    op.drop_table("traces")

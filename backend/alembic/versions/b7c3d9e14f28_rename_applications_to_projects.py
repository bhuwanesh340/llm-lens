"""rename applications to projects and add auto_created

Feature 002 (T105): renames the `applications` entity to `projects`,
repoints the `llm_requests` and `api_keys` foreign keys, and adds the
`auto_created` flag distinguishing auto-created projects (FR-106, FR-125).

Existing rows are preserved: this is a pure rename, so every historical
trace keeps its attribution.

Revision ID: b7c3d9e14f28
Revises: e12af7b507c1
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7c3d9e14f28"
down_revision: str | None = "e12af7b507c1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.rename_table("applications", "projects")
    op.execute("ALTER INDEX ix_applications_slug RENAME TO ix_projects_slug")
    op.execute("ALTER TABLE projects RENAME CONSTRAINT uq_applications_slug TO uq_projects_slug")
    op.execute("ALTER TABLE projects RENAME CONSTRAINT applications_pkey TO projects_pkey")

    op.add_column(
        "projects",
        sa.Column("auto_created", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # Traces keep SET NULL so history survives project deletion (FR-111).
    op.alter_column("llm_requests", "application_id", new_column_name="project_id")
    op.execute("ALTER INDEX ix_llm_requests_application_id RENAME TO ix_llm_requests_project_id")
    op.execute(
        "ALTER TABLE llm_requests "
        "RENAME CONSTRAINT llm_requests_application_id_fkey TO llm_requests_project_id_fkey"
    )

    # Keys are meaningless without their project, so they cascade.
    op.alter_column("api_keys", "application_id", new_column_name="project_id")
    op.execute("ALTER INDEX ix_api_keys_application_id RENAME TO ix_api_keys_project_id")
    op.drop_constraint("api_keys_application_id_fkey", "api_keys", type_="foreignkey")
    op.create_foreign_key(
        "api_keys_project_id_fkey",
        "api_keys",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("api_keys_project_id_fkey", "api_keys", type_="foreignkey")
    op.create_foreign_key(
        "api_keys_application_id_fkey",
        "api_keys",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute("ALTER INDEX ix_api_keys_project_id RENAME TO ix_api_keys_application_id")
    op.alter_column("api_keys", "project_id", new_column_name="application_id")

    op.execute(
        "ALTER TABLE llm_requests "
        "RENAME CONSTRAINT llm_requests_project_id_fkey TO llm_requests_application_id_fkey"
    )
    op.execute("ALTER INDEX ix_llm_requests_project_id RENAME TO ix_llm_requests_application_id")
    op.alter_column("llm_requests", "project_id", new_column_name="application_id")

    op.drop_column("projects", "auto_created")

    op.execute("ALTER TABLE projects RENAME CONSTRAINT projects_pkey TO applications_pkey")
    op.execute("ALTER TABLE projects RENAME CONSTRAINT uq_projects_slug TO uq_applications_slug")
    op.execute("ALTER INDEX ix_projects_slug RENAME TO ix_applications_slug")
    op.rename_table("projects", "applications")

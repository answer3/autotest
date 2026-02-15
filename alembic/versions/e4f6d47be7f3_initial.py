"""initial

Revision ID: e4f6d47be7f3
Revises: 6d4909a95f61
Create Date: 2026-01-30 23:16:34.918395

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e4f6d47be7f3"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- ENUM types (Postgres) ---

    plan_proposal_status = sa.Enum(
        "pending",
        "running",
        "succeeded",
        "failed",
        name="plan_proposal_status",
    )
    test_run_status = sa.Enum(
        "queued",
        "running",
        "passed",
        "failed",
        name="test_run_status",
    )
    """
    plan_proposal_status.create(op.get_bind(), checkfirst=True)
    test_run_status.create(op.get_bind(), checkfirst=True)
    """

    # --- test_cases ---
    op.create_table(
        "test_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
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
    )

    # --- test_case_revisions ---
    op.create_table(
        "test_case_revisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "test_case_id",
            sa.Integer(),
            sa.ForeignKey("test_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nl_text", sa.Text(), nullable=False),
        sa.Column("comment", sa.String(length=500), nullable=True),
        sa.Column("created_by", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_test_case_revisions_test_case_id", "test_case_revisions", ["test_case_id"])
    op.create_index("ix_test_case_revisions_created_at", "test_case_revisions", ["created_at"])

    # --- plan_proposals ---
    op.create_table(
        "plan_proposals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "test_case_revision_id",
            sa.Integer(),
            sa.ForeignKey("test_case_revisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status", plan_proposal_status, nullable=False, server_default=sa.text("'pending'")
        ),
        sa.Column(
            "is_ready_for_test", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("ready_for_test_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_plan_proposals_test_case_revision_id", "plan_proposals", ["test_case_revision_id"]
    )
    op.create_index("ix_plan_proposals_status", "plan_proposals", ["status"])
    op.create_index("ix_plan_proposals_is_ready_for_test", "plan_proposals", ["is_ready_for_test"])
    op.create_index("ix_plan_proposals_created_at", "plan_proposals", ["created_at"])

    op.create_index(
        "ix_plan_proposals_rev_status_created",
        "plan_proposals",
        ["test_case_revision_id", "status", "created_at"],
    )
    op.create_index(
        "ix_plan_proposals_ready_created",
        "plan_proposals",
        ["is_ready_for_test", "created_at"],
    )

    # --- test_runs ---
    op.create_table(
        "test_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "plan_proposal_id",
            sa.Integer(),
            sa.ForeignKey("plan_proposals.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", test_run_status, nullable=False, server_default=sa.text("'queued'")),
        sa.Column("run_params", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("site_domain", sa.String(length=255), nullable=True),
        sa.Column("result_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_test_runs_plan_proposal_id", "test_runs", ["plan_proposal_id"])
    op.create_index("ix_test_runs_status", "test_runs", ["status"])
    op.create_index("ix_test_runs_created_at", "test_runs", ["created_at"])
    op.create_index("ix_test_runs_started_at", "test_runs", ["started_at"])
    op.create_index("ix_test_runs_finished_at", "test_runs", ["finished_at"])
    op.create_index(
        "ix_test_runs_plan_prop_created",
        "test_runs",
        ["plan_proposal_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_test_runs_plan_prop_created", table_name="test_runs")
    op.drop_index("ix_test_runs_finished_at", table_name="test_runs")
    op.drop_index("ix_test_runs_started_at", table_name="test_runs")
    op.drop_index("ix_test_runs_created_at", table_name="test_runs")
    op.drop_index("ix_test_runs_status", table_name="test_runs")
    op.drop_index("ix_test_runs_plan_proposal_id", table_name="test_runs")
    op.drop_table("test_runs")

    op.drop_index("ix_plan_proposals_ready_created", table_name="plan_proposals")
    op.drop_index("ix_plan_proposals_rev_status_created", table_name="plan_proposals")
    op.drop_index("ix_plan_proposals_created_at", table_name="plan_proposals")
    op.drop_index("ix_plan_proposals_is_ready_for_test", table_name="plan_proposals")
    op.drop_index("ix_plan_proposals_status", table_name="plan_proposals")
    op.drop_index("ix_plan_proposals_test_case_revision_id", table_name="plan_proposals")
    op.drop_table("plan_proposals")

    op.drop_index("ix_test_case_revisions_created_at", table_name="test_case_revisions")
    op.drop_index("ix_test_case_revisions_test_case_id", table_name="test_case_revisions")
    op.drop_table("test_case_revisions")

    op.drop_table("test_cases")

    # drop enum types last
    sa.Enum(name="test_run_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="plan_proposal_status").drop(op.get_bind(), checkfirst=True)

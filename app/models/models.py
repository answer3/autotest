from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PlanProposalStatus, TestRunStatus


class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    revisions: Mapped[list["TestCaseRevision"]] = relationship(
        back_populates="test_case",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TestCaseRevision.created_at.desc()",
    )


class TestCaseRevision(Base):
    """
    Immutable revision of NL text.
    Create-only. Never update existing rows.
    """

    __tablename__ = "test_case_revisions"

    id: Mapped[int] = mapped_column(primary_key=True)

    test_case_id: Mapped[int] = mapped_column(
        ForeignKey("test_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    nl_text: Mapped[str] = mapped_column(Text, nullable=False)

    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(200), nullable=True)  # later: user id/oid

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    test_case: Mapped["TestCase"] = relationship(back_populates="revisions")

    plan_proposals: Mapped[list["PlanProposal"]] = relationship(
        back_populates="test_case_revision",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PlanProposal.created_at.desc()",
    )


class PlanProposal(Base):
    __tablename__ = "plan_proposals"

    id: Mapped[int] = mapped_column(primary_key=True)

    test_case_revision_id: Mapped[int] = mapped_column(
        ForeignKey("test_case_revisions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[PlanProposalStatus] = mapped_column(
        Enum(PlanProposalStatus, name="plan_proposal_status"),
        nullable=False,
        default=PlanProposalStatus.pending,
        index=True,
    )

    is_ready_for_test: Mapped[bool] = mapped_column(
        nullable=False,
        server_default="false",
        index=True,
    )
    ready_for_test_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    request_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    result_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    test_case_revision: Mapped["TestCaseRevision"] = relationship(back_populates="plan_proposals")

    test_runs: Mapped[list["TestRun"]] = relationship(
        back_populates="plan_proposal",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TestRun.created_at.desc()",
    )

    __table_args__ = (
        Index(
            "ix_plan_proposals_rev_status_created", "test_case_revision_id", "status", "created_at"
        ),
        Index("ix_plan_proposals_ready_created", "is_ready_for_test", "created_at"),
    )


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    plan_proposal_id: Mapped[int] = mapped_column(
        ForeignKey("plan_proposals.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status: Mapped[TestRunStatus] = mapped_column(
        Enum(TestRunStatus, name="test_run_status"),
        nullable=False,
        default=TestRunStatus.queued,
        index=True,
    )

    """
    example
    {
      "browser": "chromium",
      "headless": true,
      "timeout_ms": 30000
    }
    """
    run_params: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    site_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)

    result_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    video_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    screenshot_name: Mapped[str | None] = mapped_column(String(500), nullable=True)

    video_object_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    screenshot_object_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    created_by: Mapped[str | None] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    plan_proposal: Mapped["PlanProposal"] = relationship(back_populates="test_runs")

    __table_args__ = (
        Index("ix_test_runs_plan_prop_created", "plan_proposal_id", "created_at"),
        Index("ix_test_runs_video_name", "video_name"),
        Index("ix_test_runs_screenshot_name", "screenshot_name"),
    )

from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import Any, cast

from sqlalchemy import CursorResult, RowMapping, func, select, update
from sqlalchemy.orm import Session

from app.models.enums import PlanProposalStatus, TestRunStatus
from app.models.models import PlanProposal, TestCase, TestCaseRevision, TestRun
from app.query.filters import (
    PlanProposalListQuery,
    TestCaseListQuery,
    TestCaseRevisionListQuery,
    TestRunListQuery,
)
from app.repositories.dto import TestRunPatch
from app.repositories.query_builder import (
    apply_ilike_contains,
    apply_pagination,
    apply_range,
    apply_run_timestamps_filters,
    apply_sort,
)
from app.schemas.schemas import TestCaseCreate, TestCaseRevisionCreate, TestCaseUpdate
from app.utils import utcnow


class BaseRepository:
    def __init__(self, db: Session):
        self._db = db


class TestCaseRepository(BaseRepository):
    def get_test_case(self, test_case_id: int) -> TestCase | None:
        tc = self._db.get(TestCase, test_case_id)
        return tc

    def create_test_case(self, payload: TestCaseCreate) -> dict[str, Any] | None:
        tc = TestCase(title=payload.title, description=payload.description)
        self._db.add(tc)
        self._db.flush()

        rev = TestCaseRevision(
            test_case_id=tc.id,
            nl_text=payload.nl_text,
            comment=payload.comment,
            created_by=payload.created_by,
        )
        self._db.add(rev)
        self._db.flush()
        self._db.refresh(tc)
        return self.get_item(tc.id)

    def get_test_case_list(
        self, page: int = 1, limit: int = 20, q: TestCaseListQuery | None = None
    ) -> list[RowMapping]:
        q = q or TestCaseListQuery()
        stmt = (
            select(
                TestCase.id,
                TestCase.title,
                TestCase.description,
                TestCase.created_at,
                TestCase.updated_at,
                func.count(TestCaseRevision.id).label("revisions_count"),
                func.max(TestCaseRevision.created_at).label("last_revision_created_at"),
            )
            .outerjoin(
                TestCaseRevision,
                TestCaseRevision.test_case_id == TestCase.id,
            )
            .group_by(TestCase.id)
        )

        stmt = apply_ilike_contains(stmt, col=TestCase.title, value=q.title)
        stmt = apply_ilike_contains(stmt, col=TestCase.description, value=q.description)

        stmt = apply_range(
            stmt, col=TestCase.created_at, from_=q.created_at_from, to=q.created_at_to
        )
        stmt = apply_range(
            stmt, col=TestCase.updated_at, from_=q.updated_at_from, to=q.updated_at_to
        )

        stmt = apply_sort(
            stmt,
            sort_map={"created_at": TestCase.created_at, "updated_at": TestCase.updated_at},
            sort_by=q.sort_by,
            sort_order=q.sort_order,
            tie_breaker=TestCase.id.desc(),
        )

        stmt = apply_pagination(stmt, page=page, limit=limit)

        result = self._db.execute(stmt).mappings().all()
        return list(result)

    def get_item(self, test_case_id: int) -> dict[str, Any] | None:
        tc = self.get_test_case(test_case_id)
        if not tc:
            return None

        revisions_count = self._db.execute(
            select(func.count(TestCaseRevision.id)).where(
                TestCaseRevision.test_case_id == test_case_id
            )
        ).scalar_one()

        last_rev = (
            self._db.execute(
                select(TestCaseRevision)
                .where(TestCaseRevision.test_case_id == test_case_id)
                .order_by(TestCaseRevision.created_at.desc())
                .limit(1)
            )
            .scalars()
            .first()
        )

        return {
            "id": tc.id,
            "title": tc.title,
            "description": tc.description,
            "created_at": tc.created_at,
            "updated_at": tc.updated_at,
            "revisions_count": int(revisions_count),
            "last_revision": None
            if not last_rev
            else {
                "id": last_rev.id,
                "test_case_id": last_rev.test_case_id,
                "nl_text": last_rev.nl_text,
                "comment": last_rev.comment,
                "created_by": last_rev.created_by,
                "created_at": last_rev.created_at,
            },
        }

    def update_test_case(
        self, test_case: TestCase, payload: TestCaseUpdate
    ) -> dict[str, Any] | None:
        if payload.title is not None:
            test_case.title = payload.title
        if payload.description is not None:
            test_case.description = payload.description

        self._db.flush()
        return self.get_item(test_case.id)


class TestCaseRevisionRepository(BaseRepository):
    def create_test_case_revision(
        self, test_case_id: int, payload: TestCaseRevisionCreate
    ) -> TestCaseRevision | None:
        rev = TestCaseRevision(
            test_case_id=test_case_id,
            nl_text=payload.nl_text,
            comment=payload.comment,
            created_by=payload.created_by,
        )
        self._db.add(rev)
        self._db.flush()
        self._db.refresh(rev)
        return rev

    def get_item(self, test_case_revision_id: int) -> TestCaseRevision | None:
        return self._db.get(TestCaseRevision, test_case_revision_id)

    def get_list(
        self,
        test_case_id: int,
        page: int = 1,
        limit: int = 20,
        q: TestCaseRevisionListQuery | None = None,
    ) -> list[TestCaseRevision]:
        q = q or TestCaseRevisionListQuery()
        stmt = select(TestCaseRevision).where(TestCaseRevision.test_case_id == test_case_id)

        stmt = apply_ilike_contains(stmt, col=TestCaseRevision.nl_text, value=q.nl_text)
        stmt = apply_ilike_contains(stmt, col=TestCaseRevision.comment, value=q.comment)

        stmt = apply_range(
            stmt, col=TestCaseRevision.created_at, from_=q.created_at_from, to=q.created_at_to
        )

        stmt = apply_sort(
            stmt,
            sort_map={"created_at": TestCaseRevision.created_at},
            sort_by=q.sort_by,
            sort_order=q.sort_order,
            tie_breaker=TestCaseRevision.id.desc(),
        )

        stmt = apply_pagination(stmt, page=page, limit=limit)

        return list(self._db.execute(stmt).scalars().all())


class PlanProposalRepository(BaseRepository):
    def get_item(self, proposal_id: int) -> PlanProposal | None:
        return self._db.get(PlanProposal, proposal_id)

    def get_list(
        self,
        test_case_revision_id: int,
        page: int = 1,
        limit: int = 20,
        q: PlanProposalListQuery | None = None,
    ) -> list[PlanProposal]:
        stmt = select(PlanProposal).where(
            PlanProposal.test_case_revision_id == test_case_revision_id
        )
        q = q or PlanProposalListQuery()

        if q.statuses:
            stmt = stmt.where(PlanProposal.status.in_(q.statuses))

        if q.is_ready_for_test is not None:
            stmt = stmt.where(PlanProposal.is_ready_for_test.is_(q.is_ready_for_test))

        if q.error is not None:
            stmt = stmt.where(
                PlanProposal.error.is_not(None) if q.error else PlanProposal.error.is_(None)
            )

        stmt = apply_run_timestamps_filters(
            stmt,
            created_at=PlanProposal.created_at,
            started_at=PlanProposal.started_at,
            finished_at=PlanProposal.finished_at,
            q=q,
        )

        stmt = apply_sort(
            stmt,
            sort_map={
                "created_at": PlanProposal.created_at,
                "started_at": PlanProposal.started_at,
                "finished_at": PlanProposal.finished_at,
            },
            sort_by=q.sort_by,
            sort_order=q.sort_order,
            nulls=q.nulls,
            nulls_allowed_fields={"started_at", "finished_at"},
            tie_breaker=PlanProposal.id.desc(),
        )

        stmt = apply_pagination(stmt, page=page, limit=limit)

        return list(self._db.execute(stmt).scalars().all())

    def create(self, test_case_revision_id: int) -> PlanProposal:
        proposal = PlanProposal(
            test_case_revision_id=test_case_revision_id,
            status=PlanProposalStatus.pending,
            request_payload={"schema_version": 1, "generator": "ollama"},
        )
        self._db.add(proposal)
        self._db.flush()
        self._db.refresh(proposal)
        return proposal

    def set_is_ready_for_test(self, proposal_id: int) -> PlanProposal | None:
        stmt = (
            update(PlanProposal)
            .where(PlanProposal.id == proposal_id)
            .where(PlanProposal.status == PlanProposalStatus.succeeded)
            .values(
                is_ready_for_test=True,
                ready_for_test_at=utcnow(),
            )
        )
        self._db.execute(stmt)
        self._db.flush()
        return self.get_item(proposal_id)

    def _transition(
        self,
        proposal_id: int,
        *,
        from_statuses: Iterable[PlanProposalStatus],
        values: dict[str, Any],
    ) -> bool:
        stmt = (
            update(PlanProposal)
            .where(PlanProposal.id == proposal_id)
            .where(PlanProposal.status.in_(list(from_statuses)))
            .values(**values)
        )
        res = cast("CursorResult[Any]", self._db.execute(stmt))
        self._db.flush()
        return res.rowcount == 1

    def mark_running(self, proposal_id: int, started_at: datetime) -> bool:
        return self._transition(
            proposal_id,
            from_statuses=[PlanProposalStatus.pending],
            values={"status": PlanProposalStatus.running, "started_at": started_at},
        )

    def mark_ready(
        self, proposal_id: int, result_payload: dict[str, Any], finished_at: datetime
    ) -> bool:
        return self._transition(
            proposal_id,
            from_statuses=[PlanProposalStatus.pending, PlanProposalStatus.running],
            values={
                "status": PlanProposalStatus.succeeded,
                "result_payload": result_payload,
                "error": None,
                "finished_at": finished_at,
            },
        )

    def mark_failed(self, proposal_id: int, error: str, finished_at: datetime) -> bool:
        return self._transition(
            proposal_id,
            from_statuses=[PlanProposalStatus.pending, PlanProposalStatus.running],
            values={
                "status": PlanProposalStatus.failed,
                "error": error,
                "finished_at": finished_at,
            },
        )


class TestRunRepository(BaseRepository):
    def get_item(self, run_id: int) -> TestRun | None:
        return self._db.get(TestRun, run_id)

    def create(
        self,
        plan_proposal_id: int,
        run_params: dict[str, Any],
        created_by: str | None,
        site_domain: str | None,
    ) -> TestRun:
        tf = TestRun(
            plan_proposal_id=plan_proposal_id,
            status=TestRunStatus.queued,
            run_params=run_params,
            created_by=created_by,
            site_domain=site_domain,
        )
        self._db.add(tf)
        self._db.flush()
        self._db.refresh(tf)
        return tf

    def list(
        self,
        plan_proposal_id: int,
        page: int = 1,
        limit: int = 20,
        q: TestRunListQuery | None = None,
    ) -> list[TestRun]:
        if q is None:
            q = TestRunListQuery()

        stmt = select(TestRun).where(TestRun.plan_proposal_id == plan_proposal_id)
        if q.statuses:
            stmt = stmt.where(TestRun.status.in_(q.statuses))

        if q.error is not None:
            stmt = stmt.where(TestRun.error.is_not(None) if q.error else TestRun.error.is_(None))

        stmt = apply_ilike_contains(stmt, col=TestRun.site_domain, value=q.site_domain)

        stmt = apply_run_timestamps_filters(
            stmt,
            created_at=TestRun.created_at,
            started_at=TestRun.started_at,
            finished_at=TestRun.finished_at,
            q=q,
        )

        stmt = apply_sort(
            stmt,
            sort_map={
                "created_at": TestRun.created_at,
                "started_at": TestRun.started_at,
                "finished_at": TestRun.finished_at,
            },
            sort_by=q.sort_by,
            sort_order=q.sort_order,
            nulls=q.nulls,
            nulls_allowed_fields={"started_at", "finished_at"},
            tie_breaker=TestRun.id.desc(),
        )

        stmt = apply_pagination(stmt, page=page, limit=limit)

        return list(self._db.execute(stmt).scalars().all())

    def _transition(
        self,
        run_id: int,
        *,
        from_statuses: Sequence[TestRunStatus],
        patch: TestRunPatch,
    ) -> bool:
        values = patch.to_update_values()
        if not values:
            return False

        stmt = (
            update(TestRun)
            .where(TestRun.id == run_id)
            .where(TestRun.status.in_(from_statuses))
            .values(**values)
        )
        res = cast("CursorResult[Any]", self._db.execute(stmt))
        self._db.flush()
        return res.rowcount == 1

    def mark_running(self, run_id: int, started_at: datetime) -> bool:
        return self._transition(
            run_id,
            from_statuses=[TestRunStatus.queued],
            patch=TestRunPatch(
                status=TestRunStatus.running,
                started_at=started_at,
            ),
        )

    def mark_passed(
        self,
        run_id: int,
        result_payload: dict[str, Any],
        finished_at: datetime,
        screenshot_name: str | None = None,
        video_name: str | None = None,
        video_object_key: str | None = None,
        screenshot_object_key: str | None = None,
    ) -> bool:
        return self._transition(
            run_id,
            from_statuses=[TestRunStatus.running],
            patch=TestRunPatch(
                status=TestRunStatus.passed,
                finished_at=finished_at,
                result_payload=result_payload,
                screenshot_name=screenshot_name,
                video_name=video_name,
                video_object_key=video_object_key,
                screenshot_object_key=screenshot_object_key,
            ),
        )

    def mark_failed(
        self,
        run_id: int,
        error: str,
        finished_at: datetime,
        result_payload: dict[str, Any] | None = None,
        screenshot_name: str | None = None,
        video_name: str | None = None,
        video_object_key: str | None = None,
        screenshot_object_key: str | None = None,
    ) -> bool:
        return self._transition(
            run_id,
            from_statuses=[TestRunStatus.queued, TestRunStatus.running],
            patch=TestRunPatch(
                status=TestRunStatus.failed,
                finished_at=finished_at,
                error=error,
                result_payload=result_payload,
                screenshot_name=screenshot_name,
                video_name=video_name,
                video_object_key=video_object_key,
                screenshot_object_key=screenshot_object_key,
            ),
        )

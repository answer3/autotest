from types import TracebackType
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.repositories import (
    PlanProposalRepository,
    TestCaseRevisionRepository,
    TestRunRepository,
)


class BaseUnitOfWork:
    def __init__(self, session: Session):
        self.session = session

    def __enter__(self) -> Any:
        pass

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()


class LlmDbUnitOfWork(BaseUnitOfWork):
    def __enter__(self) -> "LlmDbUnitOfWork":
        self.plan_proposals_repo = PlanProposalRepository(self.session)
        self.test_case_revisions_repo = TestCaseRevisionRepository(self.session)
        return self


class RunnerDbUnitOfWork(BaseUnitOfWork):
    def __enter__(self) -> "RunnerDbUnitOfWork":
        self.plan_proposals_repo = PlanProposalRepository(self.session)
        self.test_runs_repo = TestRunRepository(self.session)
        return self

from sqlalchemy.orm import Session

from app.repositories.repositories import (
    PlanProposalRepository,
    TestCaseRepository,
    TestCaseRevisionRepository,
    TestRunRepository,
)


class UnitOfWork:
    def __init__(self, db: Session):
        self.db = db
        self.test_cases_repo = TestCaseRepository(db)
        self.revisions_repo = TestCaseRevisionRepository(db)
        self.plan_proposals_repo = PlanProposalRepository(db)
        self.test_runs_repo = TestRunRepository(db)

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

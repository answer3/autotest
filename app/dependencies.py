from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.artifacts.factory import build_artifact_storage
from app.artifacts.storage import ArtifactStorage
from app.core.config import settings
from app.db.session import SessionLocal
from app.queue.redis_queue import RedisPublisher
from app.repositories.repositories import (
    PlanProposalRepository,
    TestCaseRepository,
    TestCaseRevisionRepository,
    TestRunRepository,
)
from app.uow import UnitOfWork


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_uow(db: Session = Depends(get_db)) -> UnitOfWork:
    return UnitOfWork(db)


def get_redis_publisher() -> RedisPublisher:
    return RedisPublisher()


def get_test_case_repo(db: Session = Depends(get_db)) -> TestCaseRepository:
    return TestCaseRepository(db)


def get_test_case_rev_repo(db: Session = Depends(get_db)) -> TestCaseRevisionRepository:
    return TestCaseRevisionRepository(db)


def get_plan_proposal_repo(db: Session = Depends(get_db)) -> PlanProposalRepository:
    return PlanProposalRepository(db)


def get_test_run_repo(db: Session = Depends(get_db)) -> TestRunRepository:
    return TestRunRepository(db)


def get_artifact_storage() -> ArtifactStorage:
    return build_artifact_storage(settings)

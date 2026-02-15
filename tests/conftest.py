from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, PropertyMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool
from testcontainers.core.wait_strategies import LogMessageWaitStrategy
from testcontainers.postgres import PostgresContainer

from app.artifacts.artifacts_service import RunArtifactsService
from app.db.base import Base
from app.dependencies import get_db, get_redis_publisher
from app.main import app
from app.models.models import PlanProposal, TestCase, TestCaseRevision, TestRun
from app.workers.db import LlmDbUnitOfWork, RunnerDbUnitOfWork


@pytest.fixture(scope="session")
def postgres_container():
    with (
            PostgresContainer("postgres:16-alpine")
                    .waiting_for(
                LogMessageWaitStrategy("ready")
            )
    ) as pg:
        yield pg


@pytest.fixture(scope="session")
def engine(postgres_container):
    db_url = postgres_container.get_connection_url()  # e.g. postgresql://test:test@localhost:...
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    engine_ = create_engine(
        db_url,
        future=True,
        poolclass=NullPool,
    )

    yield engine_

    engine_.dispose()


@pytest.fixture(scope="session", autouse=True)
def create_schema(engine):
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(engine) -> Session:
    connection = engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        future=True,
    )
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


class FakeRedisPublisher:
    def __init__(self):
        self.proposal_calls = []
        self.test_run_calls = []

    def publish_plan_generation(self, payload: dict) -> None:
        self.proposal_calls.append(payload)

    def publish_test_run(self, payload: dict) -> None:
        self.test_run_calls.append(payload)


@pytest.fixture()
def publisher():
    return FakeRedisPublisher()


class FakeArtifactStorage:
    def __init__(self, *, presign_url: str | None = None, local_root: Path | None = None):
        self._presign_url = presign_url
        self._local_root = local_root

    def presign_get_url(self, *, object_key: str, expires: timedelta):
        return self._presign_url

    def get_local_path(self, *, object_key: str):
        if self._local_root is None:
            return None
        return self._local_root / object_key


@pytest.fixture()
def client(db_session: Session, publisher: FakeRedisPublisher):
    def _get_db_override():
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = _get_db_override
    app.dependency_overrides[get_redis_publisher] = lambda: publisher

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture()
def llm_uow_factory(db_session):
    return lambda: LlmDbUnitOfWork(db_session)


@pytest.fixture()
def runner_uow_factory(db_session):
    return lambda: RunnerDbUnitOfWork(db_session)


def create_test_case(
        client: TestClient,
        payload: dict,
) -> dict:
    r = client.post("/test-cases", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def make_test_case(db: Session, **kwargs) -> TestCase:
    obj = TestCase(**kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def make_revision(db: Session, test_case_id: int, **kwargs) -> TestCaseRevision:
    obj = TestCaseRevision(test_case_id=test_case_id, **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def make_test_case_and_revision(db: Session, **kwargs) -> TestCase:
    tc = make_test_case(
        db,
        title=kwargs["title"],
        description=kwargs["description"],
    )

    make_revision(
        db=db,
        test_case_id=tc.id,
        nl_text=kwargs["nl_text"],
        comment=kwargs["comment"],
        created_by=kwargs["created_by"],
    )

    db.flush()
    return tc


def make_plan_proposal(
        db: Session,
        revision_id: int,
        **kwargs
) -> PlanProposal:
    proposal = PlanProposal(
        test_case_revision_id=revision_id,
        **kwargs
    )
    db.add(proposal)
    db.flush()
    db.refresh(proposal)
    return proposal


def make_test_case_revision_proposal(db: Session, test_case_revision: dict, plan_proposal: dict) -> (
        TestCase, PlanProposal):
    tc = make_test_case(
        db,
        title=test_case_revision["title"],
        description=test_case_revision["description"],
    )

    rev = make_revision(
        db=db,
        test_case_id=tc.id,
        nl_text=test_case_revision["nl_text"],
        comment=test_case_revision["comment"],
        created_by=test_case_revision["created_by"],
    )

    prop = make_plan_proposal(
        db=db,
        revision_id=rev.id,
        **plan_proposal
    )

    db.flush()
    return tc, prop


def make_test_run(
        db: Session,
        plan_proposal_id: int,
        **kwargs
) -> TestRun:
    tr = TestRun(
        plan_proposal_id=plan_proposal_id,
        **kwargs
    )
    db.add(tr)
    db.flush()
    db.refresh(tr)
    return tr


class _ExpectPage:
    def __init__(self):
        self.calls = []

    async def to_have_url(self, url_or_re):
        self.calls.append(("to_have_url", url_or_re))


class _ExpectLocator:
    def __init__(self):
        self.calls = []

    async def to_be_visible(self):
        self.calls.append(("to_be_visible", None))

    async def to_contain_text(self, text: str):
        self.calls.append(("to_contain_text", text))


class FakeExpectPlaywright:
    def __init__(self, page, locator):
        self._page = page
        self._locator = locator
        self.page_matcher = _ExpectPage()
        self.locator_matcher = _ExpectLocator()

    def __call__(self, obj):
        if obj is self._page:
            return self.page_matcher
        if obj is self._locator:
            return self.locator_matcher
        raise AssertionError(f"Unexpected expect() target: {obj!r}")


class FakeSessionFactory:
    """
    Fake for PlaywrightSessionFactory:
      - session(): yields (PlaywrightSession-like, artifacts-like)
      - make_screenshot(): returns configured name or raises
      - properties used in RunTestOutput
    """

    def __init__(self, page, screenshot_name="shot.png", video_name="vid.webm", make_screenshot_raises=False):
        self._page = page
        self._screenshot_name = screenshot_name
        self._video_name = video_name
        self._make_screenshot_raises = make_screenshot_raises

        self._browser_name = "chromium"
        self._headless = True
        self._timeout_ms = 1234.0

    @property
    def browser_name(self) -> str:
        return self._browser_name

    @property
    def headless(self) -> bool:
        return self._headless

    @property
    def timeout_ms(self) -> float:
        return self._timeout_ms

    async def make_screenshot(self, *, page, run_id: int):
        if self._make_screenshot_raises:
            raise RuntimeError("screenshot failed")
        return self._screenshot_name

    @asynccontextmanager
    async def session(self, *, base_url: str, run_id: int):
        # emulate PlaywrightSession + SessionArtifacts objects
        s = SimpleNamespace(page=self._page)
        artifacts = SimpleNamespace(video_name=self._video_name, screenshot_name=None)
        yield s, artifacts


def make_page(*, url: str = "https://final", url_raises: bool = False) -> AsyncMock:
    page = AsyncMock()

    # playwright page.url is a property (sync)
    if url_raises:
        def _boom():
            raise RuntimeError("url property failed")

        type(page).url = PropertyMock(side_effect=_boom)
    else:
        type(page).url = PropertyMock(return_value=url)

    page.locator = Mock(return_value=object())
    return page


@pytest.fixture()
def artifacts_service_factory(tmp_path):

    def factory():
        svc = RunArtifactsService(
            storage=FakeArtifactStorage(local_root=tmp_path),
            local_root=tmp_path,
            cleanup_local_after_upload=False,
        )

        svc.upload_calls = []

        def fake_upload_run_artifacts(*, run_id, video_name, screenshot_name):
            svc.upload_calls.append((run_id, video_name, screenshot_name))
            return SimpleNamespace(
                video_object_key="obj/video.webm",
                screenshot_object_key="obj/shot.png",
            )

        svc.upload_run_artifacts = fake_upload_run_artifacts
        return svc

    return factory

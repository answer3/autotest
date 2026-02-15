from app.dependencies import get_artifact_storage
from app.main import app
from tests.conftest import FakeArtifactStorage, make_test_case_revision_proposal, make_test_run
from tests.data.data_proposals import PROPOSAL_DATA_SUCCESS_READY_1
from tests.data.data_test_case import TEST_CASE_REQUEST_1
from tests.data.data_test_run import TEST_RUN_DATA_CREATE_PASSED_1


def test_get_video_404_run_not_found(client):
    r = client.get("/test-runs/999999/artifacts/video")
    assert r.status_code == 404
    assert r.json()["detail"] == "run does not exists"


def test_get_video_404_video_not_available(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)
    run = make_test_run(db_session, plan_proposal_id=proposal.id, video_name=None, **TEST_RUN_DATA_CREATE_PASSED_1)

    r = client.get(f"/test-runs/{run.id}/artifacts/video")
    assert r.status_code == 404
    assert r.json()["detail"] == "video not available"


def test_get_video_redirects_to_presigned_url(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)
    run = make_test_run(db_session, plan_proposal_id=proposal.id, video_name="vid.webm", **TEST_RUN_DATA_CREATE_PASSED_1)

    app.dependency_overrides[get_artifact_storage] = lambda: FakeArtifactStorage(presign_url="https://minio.local/presigned")

    try:
        r = client.get(f"/test-runs/{run.id}/artifacts/video", follow_redirects=False)
        assert r.status_code in (302, 307)
        assert r.headers["location"] == "https://minio.local/presigned"
    finally:
        app.dependency_overrides.pop(get_artifact_storage, None)


def test_get_video_serves_local_file_when_no_presign(client, db_session, tmp_path):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)
    run = make_test_run(
        db_session,
        plan_proposal_id=proposal.id,
        video_name="vid.webm",
        video_object_key="runs/1/video/vid.webm",
        **TEST_RUN_DATA_CREATE_PASSED_1
    )

    file_path = tmp_path / "runs/1/video"
    file_path.mkdir(parents=True, exist_ok=True)
    (file_path / "vid.webm").write_bytes(b"WEBM")

    app.dependency_overrides[get_artifact_storage] = lambda: FakeArtifactStorage(presign_url=None, local_root=tmp_path)
    try:
        r = client.get(f"/test-runs/{run.id}/artifacts/video")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("video/webm")
        assert r.content == b"WEBM"
    finally:
        app.dependency_overrides.pop(get_artifact_storage, None)


def test_get_video_404_if_local_file_missing(client, db_session, tmp_path):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)
    run = make_test_run(
        db_session,
        plan_proposal_id=proposal.id,
        video_name="vid.webm",
        video_object_key="runs/1/video/vid.webm",
        **TEST_RUN_DATA_CREATE_PASSED_1
    )

    app.dependency_overrides[get_artifact_storage] = lambda: FakeArtifactStorage(presign_url=None, local_root=tmp_path)

    try:
        r = client.get(f"/test-runs/{run.id}/artifacts/video")
        assert r.status_code == 404
        assert r.json()["detail"] == "artifact file not found"
    finally:
        app.dependency_overrides.pop(get_artifact_storage, None)


def test_get_screenshot_404_run_not_found(client):
    r = client.get("/test-runs/999999/artifacts/screenshot")
    assert r.status_code == 404
    assert r.json()["detail"] == "run does not exists"


def test_get_screenshot_404_not_available(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)
    run = make_test_run(
        db_session,
        plan_proposal_id=proposal.id,
        screenshot_name=None,
        **TEST_RUN_DATA_CREATE_PASSED_1
    )

    r = client.get(f"/test-runs/{run.id}/artifacts/screenshot")
    assert r.status_code == 404
    assert r.json()["detail"] == "screenshot not available"


def test_get_screenshot_redirects_to_presigned_url(client, db_session):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)
    run = make_test_run(
        db_session,
        plan_proposal_id=proposal.id,
        screenshot_name="shot.png",
        **TEST_RUN_DATA_CREATE_PASSED_1
    )

    app.dependency_overrides[get_artifact_storage] = lambda: FakeArtifactStorage(
        presign_url="https://minio.local/presigned-shot"
    )

    try:
        r = client.get(f"/test-runs/{run.id}/artifacts/screenshot", follow_redirects=False)
        assert r.status_code in (302, 307)
        assert r.headers["location"] == "https://minio.local/presigned-shot"
    finally:
        app.dependency_overrides.pop(get_artifact_storage, None)


def test_get_screenshot_serves_local_file_when_no_presign(client, db_session, tmp_path):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)
    run = make_test_run(
        db_session,
        plan_proposal_id=proposal.id,
        screenshot_name="shot.png",
        screenshot_object_key="runs/1/screenshot/shot.png",
        **TEST_RUN_DATA_CREATE_PASSED_1
    )

    p = tmp_path / "runs/1/screenshot"
    p.mkdir(parents=True, exist_ok=True)
    (p / "shot.png").write_bytes(b"\x89PNG\r\n")

    fake_storage = FakeArtifactStorage(presign_url=None, local_root=tmp_path)

    app.dependency_overrides[get_artifact_storage] = lambda: fake_storage
    try:
        r = client.get(f"/test-runs/{run.id}/artifacts/screenshot")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("image/png")
        assert r.content.startswith(b"\x89PNG")
    finally:
        app.dependency_overrides.pop(get_artifact_storage, None)

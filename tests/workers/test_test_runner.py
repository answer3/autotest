import json

from app.models.enums import TestRunStatus
from app.workers.run_test_worker import handle_message
from app.workers.test_runner.dto import PlanExecutionFailed, RunTestOutput
from tests.conftest import make_test_case_revision_proposal, make_test_run
from tests.data.data_proposals import PROPOSAL_DATA_SUCCESS_READY_1
from tests.data.data_test_case import TEST_CASE_REQUEST_1
from tests.data.data_test_run import TEST_RUN_PARAMS


def _msg(run_id: int, placeholders: str | None = None) -> bytes:
    payload = {"run_id": run_id}
    if placeholders is not None:
        payload["placeholders"] = placeholders
    return json.dumps(payload).encode("utf-8")


def test_handle_message_success_marks_passed_and_uploads(
        db_session,
        runner_uow_factory,
        artifacts_service_factory,
):
    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)
    run = make_test_run(db_session, plan_proposal_id=proposal.id, run_params=TEST_RUN_PARAMS,
                        site_domain="https://example.com")
    run_id = run.id

    # --- fake executor ---
    calls = []

    def execute_plan_fn(run_params, plan, base_url, run_id_arg, artifacts_root):
        calls.append((run_params, base_url, run_id_arg, artifacts_root))
        return RunTestOutput(
            status=TestRunStatus.passed,
            final_url="https://final/success",
            executed_steps=["step1", "step2"],
            executed_assertions=["assert1"],
            timeout_ms=float(run_params["playwright_timeout_ms"]),
            browser=str(run_params["playwright_browser"]),
            headless=bool(run_params["playwright_headless"]),
            video_name="vid.webm",
            screenshot_name="shot.png",
        )

    svc = artifacts_service_factory()

    # --- act ---
    handle_message(
        _msg(run_id, placeholders="{}"),
        run_uow_factory=runner_uow_factory,
        artifacts_service_factory=lambda: svc,
        execute_plan_fn=execute_plan_fn,
    )

    # --- assert execute_plan called ---
    assert len(calls) == 1
    assert calls[0][2] == run_id

    # --- assert upload called ---
    assert svc.upload_calls == [(run_id, "vid.webm", "shot.png")]

    with runner_uow_factory() as uow:
        run = uow.test_runs_repo.get_item(run_id)

        assert run.status == TestRunStatus.passed
        assert run.video_name == "vid.webm"
        assert run.screenshot_name == "shot.png"
        assert run.video_object_key == "obj/video.webm"
        assert run.screenshot_object_key == "obj/shot.png"

        assert run.result_payload["final_url"] == "https://final/success"
        assert run.result_payload["executed_steps"] == ["step1", "step2"]
        assert run.result_payload["executed_assertions"] == ["assert1"]


def test_handle_message_plan_execution_failed_marks_failed_and_uploads(
        db_session,
        runner_uow_factory,
        artifacts_service_factory,
):
    """
    with runner_uow_factory() as uow:
        prop = uow.plan_proposals_repo.create_item(result_payload={"steps": []})
        run = uow.test_runs_repo.create_item(
            status=TestRunStatus.created,
            site_domain="example.com",
            plan_proposal_id=prop.id,
            run_params={
                "playwright_browser": "chromium",
                "playwright_timeout_ms": 1000,
                "playwright_headless": True,
            },
        )
        run_id = run.id
    """

    tc, proposal = make_test_case_revision_proposal(db_session, TEST_CASE_REQUEST_1, PROPOSAL_DATA_SUCCESS_READY_1)
    run = make_test_run(db_session, plan_proposal_id=proposal.id, run_params=TEST_RUN_PARAMS,
                        site_domain="https://example.com")
    run_id = run.id

    def execute_plan_fn(run_params, plan, base_url, run_id_arg, artifacts_root):
        result = RunTestOutput(
            status=TestRunStatus.failed,
            final_url="https://final/failed",
            executed_steps=["step1"],
            executed_assertions=["assert1"],
            timeout_ms=float(run_params["playwright_timeout_ms"]),
            browser=str(run_params["playwright_browser"]),
            headless=bool(run_params["playwright_headless"]),
            video_name=None,
            screenshot_name="shot.png",
        )
        raise PlanExecutionFailed(result=result, original_exc=Exception("boom"))

    svc = artifacts_service_factory()

    handle_message(
        _msg(run_id),
        run_uow_factory=runner_uow_factory,
        artifacts_service_factory=lambda: svc,
        execute_plan_fn=execute_plan_fn,
    )

    assert svc.upload_calls == [(run_id, None, "shot.png")]

    with runner_uow_factory() as uow:
        run = uow.test_runs_repo.get_item(run_id)

        assert run.status == TestRunStatus.failed
        assert "execution_failed" in (run.error or "")

        assert run.video_object_key == "obj/video.webm"
        assert run.screenshot_object_key == "obj/shot.png"

        assert run.result_payload["final_url"] == "https://final/failed"
        assert run.result_payload["executed_steps"] == ["step1"]
        assert run.result_payload["executed_assertions"] == ["assert1"]

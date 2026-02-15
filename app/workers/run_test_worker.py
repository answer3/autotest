import asyncio
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.artifacts.artifacts_service import RunArtifactsService
from app.artifacts.factory import build_artifact_storage
from app.core.config import settings
from app.core.logging import setup_logger
from app.models.enums import TestRunStatus
from app.queue.redis_consumer import RedisConsumer
from app.utils import utcnow
from app.workers.db import RunnerDbUnitOfWork
from app.workers.test_runner.dto import (
    PlanExecutionFailed,
    PlanPayload,
    PlaywrightRunnerConfig,
    RunTestOutput,
)
from app.workers.test_runner.playwright_run import PlaywrightRunner, PlaywrightSessionFactory
from app.workers.test_runner.renderer import normalize_base_url, parse_placeholders, render_plan


def execute_plan_prod(
    run_params: dict[str, Any], plan: PlanPayload, base_url: str, run_id: int, artifacts_root: Path
) -> RunTestOutput:
    pw_factory = PlaywrightSessionFactory(
        PlaywrightRunnerConfig(
            browser_name=str(run_params["playwright_browser"]),
            timeout_ms=float(run_params["playwright_timeout_ms"]),
            headless=bool(run_params["playwright_headless"]),
            artifacts_root=artifacts_root,
        )
    )
    return asyncio.run(
        PlaywrightRunner(pw_factory).execute_plan(plan, base_url=base_url, run_id=run_id)
    )


def handle_message(
    body: bytes,
    run_uow_factory: Callable[[], RunnerDbUnitOfWork],
    artifacts_service_factory: Callable[[], RunArtifactsService],
    execute_plan_fn: Callable[..., Any],
) -> None:
    payload = json.loads(body.decode("utf-8"))
    run_id = int(payload["run_id"])
    logger.info("Run Test Worker: message received run_id={}", run_id)

    placeholders_raw = payload.get("placeholders") or "{}"
    placeholders = parse_placeholders(placeholders_raw)
    if not placeholders:
        logger.warning("Run Test Worker: using empty placeholders")
    with run_uow_factory() as run_uow:
        try:
            run = run_uow.test_runs_repo.get_item(run_id)
            if not run:
                logger.warning("Run Test Worker: test_run not found run_id={}", run_id)
                return

            if run.status in (TestRunStatus.passed, TestRunStatus.failed):
                logger.info(
                    "Run Test Worker: test_run already finished run_id={} status={}",
                    run_id,
                    run.status,
                )
                return

            try:
                base_url = normalize_base_url(run.site_domain or "")
                logger.info(f"site_domain: {base_url}")
            except Exception as e:
                logger.error(f"invalid_site_domain: {e}")
                run_uow.test_runs_repo.mark_failed(
                    run_id, error=f"invalid_site_domain: {e}", finished_at=utcnow()
                )
                return

            ok = run_uow.test_runs_repo.mark_running(run_id, started_at=utcnow())
            if not ok:
                logger.warning("Run Test Worker: cannot mark running run_id={}", run_id)
                return

            plan_prop = run_uow.plan_proposals_repo.get_item(run.plan_proposal_id)
            if not plan_prop:
                logger.error("plan_proposal not found")
                run_uow.test_runs_repo.mark_failed(
                    run_id, error="plan_proposal not found", finished_at=utcnow()
                )
                return

            try:
                rendered_dict = render_plan(plan_prop.result_payload, placeholders)
            except Exception as e:
                logger.error(f"params_substitution_error: {e}")
                run_uow.test_runs_repo.mark_failed(
                    run_id, error=f"params_substitution_error: {e}", finished_at=utcnow()
                )
                return

            try:
                plan = PlanPayload.from_any(rendered_dict)
            except Exception as e:
                logger.error(f"invalid_plan_payload: {e}")
                run_uow.test_runs_repo.mark_failed(
                    run_id, error=f"invalid_plan_payload: {e}", finished_at=utcnow()
                )
                return

            artifacts_service = artifacts_service_factory()

            try:
                """
                playwright_factory = PlaywrightSessionFactory(
                    PlaywrightRunnerConfig(
                        browser_name=str(run.run_params["playwright_browser"]),
                        timeout_ms=float(run.run_params["playwright_timeout_ms"]),
                        headless=bool(run.run_params["playwright_headless"]),
                        artifacts_root=artifacts_service.local_root_dir,
                    )
                )

                result = asyncio.run(
                    PlaywrightRunner(playwright_factory).execute_plan(
                        plan,
                        base_url=base_url,
                        run_id=run_id,
                    )
                )
                """
                result = execute_plan_fn(
                    run.run_params, plan, base_url, run_id, artifacts_service.local_root_dir
                )
                uploaded = artifacts_service.upload_run_artifacts(
                    run_id=run_id,
                    video_name=result.video_name,
                    screenshot_name=result.screenshot_name,
                )

                run_uow.test_runs_repo.mark_passed(
                    run_id=run_id,
                    result_payload={
                        "final_url": result.final_url,
                        "executed_steps": result.executed_steps,
                        "executed_assertions": result.executed_assertions,
                    },
                    video_name=result.video_name,
                    screenshot_name=result.screenshot_name,
                    video_object_key=uploaded.video_object_key,
                    screenshot_object_key=uploaded.screenshot_object_key,
                    finished_at=utcnow(),
                )
                logger.info(
                    "Run Test Worker: finished run_id={} status=passed final_url={}",
                    run_id,
                    result.final_url,
                )

            except PlanExecutionFailed as e:
                result = e.result

                uploaded = artifacts_service.upload_run_artifacts(
                    run_id=run_id,
                    video_name=result.video_name,
                    screenshot_name=result.screenshot_name,
                )

                run_uow.test_runs_repo.mark_failed(
                    run_id,
                    error=f"execution_failed: {e}",
                    result_payload={
                        "final_url": result.final_url,
                        "executed_steps": result.executed_steps,
                        "executed_assertions": result.executed_assertions,
                    },
                    finished_at=utcnow(),
                    screenshot_name=result.screenshot_name,
                    video_name=result.video_name,
                    video_object_key=uploaded.video_object_key,
                    screenshot_object_key=uploaded.screenshot_object_key,
                )
                logger.info(
                    "Run Test Worker: finished run_id={} status=failed final_url={}",
                    run_id,
                    result.final_url,
                )

        except Exception:
            logger.exception("Run Test Worker: unexpected crash run_id={}", run_id)
            raise


def main() -> None:
    setup_logger()
    consumer = RedisConsumer("test_runner")
    engine = create_engine(settings.database_url, future=True)
    db_sessionmaker = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    storage = build_artifact_storage(settings)

    consumer.consume(
        lambda msg: handle_message(
            msg,
            lambda: RunnerDbUnitOfWork(db_sessionmaker()),
            lambda: RunArtifactsService(
                storage=storage,
                local_root=settings.artifacts_root_dir_path,
                cleanup_local_after_upload=True,
            ),
            execute_plan_fn=execute_plan_prod,
        )
    )


if __name__ == "__main__":
    main()

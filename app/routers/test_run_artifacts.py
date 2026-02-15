from datetime import timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from starlette.responses import FileResponse, RedirectResponse, Response

from app.artifacts.keys import screenshot_key, video_key
from app.artifacts.storage import ArtifactStorage
from app.core.config import settings
from app.dependencies import get_artifact_storage, get_test_run_repo
from app.repositories.repositories import TestRunRepository
from app.workers.test_runner.artifacts import screenshot_path, video_path

router = APIRouter(tags=["Test run artifacts"])


def _pick_object_key(
    *,
    explicit_key: str | None,
    computed_key: str,
) -> str:
    return explicit_key or computed_key


def _maybe_presign_or_local(
    *,
    storage: ArtifactStorage,
    object_key: str,
    fallback_local_path: Path,
    filename: str,
    media_type: str,
    presign_ttl: timedelta = timedelta(minutes=30),
) -> Response:
    # 1) Remote storage path via presigned URL
    url = storage.presign_get_url(object_key=object_key, expires=presign_ttl)
    if url:
        # 302 redirect to MinIO/S3
        return RedirectResponse(url)

    # 2) Local FS path
    local_path = storage.get_local_path(object_key=object_key)
    if local_path is None:
        local_path = fallback_local_path

    if not local_path.exists():
        raise HTTPException(status_code=404, detail="artifact file not found")

    return FileResponse(
        path=str(local_path),
        media_type=media_type,
        filename=filename,
    )


@router.get("/test-runs/{run_id}/artifacts/video")
def get_test_run_video(
    run_id: int,
    storage: ArtifactStorage = Depends(get_artifact_storage),
    test_run_repo: TestRunRepository = Depends(get_test_run_repo),
) -> Response:
    run = test_run_repo.get_item(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run does not exists")
    if not run.video_name:
        raise HTTPException(status_code=404, detail="video not available")

    object_key = _pick_object_key(
        explicit_key=getattr(run, "video_object_key", None),
        computed_key=video_key(run_id, str(run.video_name)),
    )

    fallback = video_path(settings.artifacts_root_dir_path, run_id, str(run.video_name))

    return _maybe_presign_or_local(
        storage=storage,
        object_key=object_key,
        fallback_local_path=fallback,
        filename=str(run.video_name),
        media_type="video/webm",
    )


@router.get("/test-runs/{run_id}/artifacts/screenshot")
def get_test_run_screenshot(
    run_id: int,
    test_run_repo: TestRunRepository = Depends(get_test_run_repo),
    storage: ArtifactStorage = Depends(get_artifact_storage),
) -> Response:
    run = test_run_repo.get_item(run_id)

    if not run:
        raise HTTPException(status_code=404, detail="run does not exists")
    if not run.screenshot_name:
        raise HTTPException(status_code=404, detail="screenshot not available")

    object_key = _pick_object_key(
        explicit_key=getattr(run, "screenshot_object_key", None),
        computed_key=screenshot_key(run_id, str(run.screenshot_name)),
    )

    fallback = screenshot_path(settings.artifacts_root_dir_path, run_id, str(run.screenshot_name))

    return _maybe_presign_or_local(
        storage=storage,
        object_key=object_key,
        fallback_local_path=fallback,
        filename=str(run.screenshot_name),
        media_type="image/png",
    )

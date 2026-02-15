from dataclasses import dataclass
from pathlib import Path

from app.artifacts.keys import screenshot_key, video_key
from app.artifacts.storage import ArtifactStorage
from app.workers.test_runner.artifacts import screenshot_path, video_path


@dataclass(frozen=True)
class UploadedArtifacts:
    video_object_key: str | None = None
    screenshot_object_key: str | None = None


class RunArtifactsService:
    def __init__(
        self,
        *,
        storage: ArtifactStorage,
        local_root: Path,
        cleanup_local_after_upload: bool = True,
    ) -> None:
        self._storage = storage
        self._local_root = local_root.resolve()
        self._cleanup = cleanup_local_after_upload and (not storage.is_local)

    @property
    def local_root_dir(self) -> Path:
        return self._local_root

    def _cleanup_local(self, local_file: Path) -> None:
        try:
            local_file.unlink(missing_ok=True)
            local_file.parent.rmdir()
        except OSError:
            pass

    def upload_run_artifacts(
        self,
        *,
        run_id: int,
        video_name: str | None,
        screenshot_name: str | None,
    ) -> UploadedArtifacts:
        video_obj_key = None
        screenshot_obj_key = None

        # backend=local -> no-op
        if self._storage.is_local:
            if video_name:
                video_obj_key = video_key(run_id, video_name)
            if screenshot_name:
                screenshot_obj_key = screenshot_key(run_id, screenshot_name)
            return UploadedArtifacts(
                video_object_key=video_obj_key, screenshot_object_key=screenshot_obj_key
            )

        # ---- remote storage upload ----
        if video_name:
            local_video = video_path(self._local_root, run_id, video_name)
            if local_video.exists():
                video_obj_key = video_key(run_id, video_name)
                self._storage.put_file(
                    object_key=video_obj_key,
                    file_path=local_video,
                    content_type="video/webm",
                )
                if self._cleanup:
                    self._cleanup_local(local_file=local_video)

        if screenshot_name:
            local_img = screenshot_path(self._local_root, run_id, screenshot_name)
            if local_img.exists():
                screenshot_obj_key = screenshot_key(run_id, screenshot_name)
                self._storage.put_file(
                    object_key=screenshot_obj_key,
                    file_path=local_img,
                    content_type="image/png",
                )
                if self._cleanup:
                    self._cleanup_local(local_file=local_img)

        return UploadedArtifacts(
            video_object_key=video_obj_key, screenshot_object_key=screenshot_obj_key
        )

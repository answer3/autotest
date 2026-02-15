import shutil
from datetime import timedelta
from pathlib import Path

from app.artifacts.storage import ArtifactStorage


class LocalFSArtifactStorage(ArtifactStorage):
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir.resolve()
        self.root_dir.mkdir(parents=True, exist_ok=True)

    @property
    def is_local(self) -> bool:
        return True

    def _abs_path(self, object_key: str) -> Path:
        return (self.root_dir / object_key).resolve()

    def put_file(self, *, object_key: str, file_path: Path, content_type: str) -> None:
        dst = self._abs_path(object_key)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, dst)

    def exists(self, *, object_key: str) -> bool:
        return self._abs_path(object_key).exists()

    def delete(self, *, object_key: str) -> None:
        p = self._abs_path(object_key)
        if p.exists():
            p.unlink()

    def get_local_path(self, *, object_key: str) -> Path | None:
        p = self._abs_path(object_key)
        return p if p.exists() else None

    def presign_get_url(self, *, object_key: str, expires: timedelta) -> str | None:
        return None

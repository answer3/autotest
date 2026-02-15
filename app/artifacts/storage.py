from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class StoredObject:
    object_key: str
    filename: str
    content_type: str


class ArtifactStorage(Protocol):
    @property
    def is_local(self) -> bool: ...

    def put_file(
        self,
        *,
        object_key: str,
        file_path: Path,
        content_type: str,
    ) -> None: ...

    def exists(self, *, object_key: str) -> bool: ...

    def delete(self, *, object_key: str) -> None: ...

    def get_local_path(self, *, object_key: str) -> Path | None: ...

    def presign_get_url(self, *, object_key: str, expires: timedelta) -> str | None: ...

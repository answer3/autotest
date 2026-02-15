import contextlib
from datetime import timedelta
from pathlib import Path

from minio import Minio

from app.artifacts.storage import ArtifactStorage


class MinioArtifactStorage(ArtifactStorage):
    def __init__(self, client: Minio, bucket: str) -> None:
        self.client = client
        self.bucket = bucket

    @property
    def is_local(self) -> bool:
        return False

    def put_file(self, *, object_key: str, file_path: Path, content_type: str) -> None:
        self.client.fput_object(
            bucket_name=self.bucket,
            object_name=object_key,
            file_path=str(file_path),
            content_type=content_type,
        )

    def exists(self, *, object_key: str) -> bool:
        try:
            self.client.stat_object(self.bucket, object_key)
            return True
        except Exception:
            return False

    def delete(self, *, object_key: str) -> None:
        with contextlib.suppress(Exception):
            self.client.remove_object(self.bucket, object_key)

    def get_local_path(self, *, object_key: str) -> Path | None:
        return None

    def presign_get_url(self, *, object_key: str, expires: timedelta) -> str | None:
        return self.client.presigned_get_object(
            bucket_name=self.bucket,
            object_name=object_key,
            expires=expires,
        )

from pathlib import Path

from minio import Minio

from app.core.config import Settings


def get_minio_client(settings: Settings) -> Minio:
    return Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def minio_upload_file(
    client: Minio,
    *,
    bucket: str,
    object_name: str,
    file_path: Path,
    content_type: str,
) -> None:
    client.fput_object(
        bucket_name=bucket,
        object_name=object_name,
        file_path=str(file_path),
        content_type=content_type,
    )

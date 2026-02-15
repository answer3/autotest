from pathlib import Path

from app.artifacts.local_fs import LocalFSArtifactStorage
from app.artifacts.minio_storage import MinioArtifactStorage
from app.artifacts.storage import ArtifactStorage
from app.clients.minio_client import get_minio_client
from app.core.config import Settings


def build_artifact_storage(settings: Settings) -> ArtifactStorage:
    """
    settings.storage_backend: "local" | "minio"
    settings.artifacts_dir: Path
    settings.minio_endpoint, minio_access_key, minio_secret_key, minio_secure, minio_bucket
    """
    backend = getattr(settings, "storage_backend", "local")

    if backend == "local":
        return LocalFSArtifactStorage(Path(settings.artifacts_root_dir_path))

    if backend == "minio":
        client = get_minio_client(settings)
        return MinioArtifactStorage(client=client, bucket=settings.minio_bucket)

    raise ValueError(f"Unsupported storage backend: {backend}")

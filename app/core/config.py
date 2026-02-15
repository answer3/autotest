from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
    )

    database_url: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    num_predict: int = 400

    redis_url: str = "redis://localhost:6379/0"
    redis_llm_stream: str = "llm_jobs"
    redis_llm_group: str = "llm_workers"
    redis_llm_consumer: str = "llm_worker_1"

    redis_test_run_stream: str = "test_run_jobs"
    redis_test_group: str = "test_run_workers"
    redis_test_consumer: str = "test_run_worker_1"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "test-artifacts"
    minio_secure: bool = False

    artifacts_root: str | None = None

    storage_backend: Literal["minio", "local"] = "local"

    @property
    def artifacts_root_dir_path(self) -> Path:
        return Path("/tmp") if not self.artifacts_root else Path(self.artifacts_root)

    log_level: str = "INFO"
    log_file: str = "./logs/app.log"


settings = Settings()

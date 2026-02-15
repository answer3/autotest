from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class TestRunPatch:
    status: Any | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    result_payload: dict[str, Any] | None = None
    screenshot_name: str | None = None
    video_name: str | None = None
    video_object_key: str | None = None
    screenshot_object_key: str | None = None

    def to_update_values(self) -> dict[str, Any]:
        data = self.__dict__
        return {k: v for k, v in data.items() if v is not None}

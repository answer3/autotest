import json
from typing import Any

import redis

from app.core.config import settings


class RedisPublisher:
    def __init__(self, redis_url: str | None = None):
        self._r = redis.Redis.from_url(
            redis_url or settings.redis_url,
            decode_responses=True,
        )

    def publish_plan_generation(self, message: dict[Any, Any]) -> Any:
        """
        message: {"proposal_id": int}
        """
        if "proposal_id" not in message:
            raise ValueError("proposal_id is required")

        return self._r.xadd(
            settings.redis_llm_stream,
            {"proposal_id": str(message["proposal_id"])},
        )

    def publish_test_run(self, message: dict[Any, Any]) -> Any:
        """
        message: {"run_id": int, "placeholders": dict}
        """
        if "run_id" not in message:
            raise ValueError("run_id is required")

        return self._r.xadd(
            settings.redis_test_run_stream,
            {
                "run_id": str(message["run_id"]),
                "placeholders": json.dumps(message.get("placeholders", {}), ensure_ascii=False),
            },
        )

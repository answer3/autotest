import json
import time
from collections.abc import Callable
from typing import Literal

import redis

from app.core.config import settings

WorkerType = Literal["llm", "test_runner"]


class RedisConsumer:
    def __init__(self, worker_type: WorkerType, redis_url: str | None = None):
        self._redis_url = redis_url or settings.redis_url
        self._r = redis.Redis.from_url(self._redis_url, decode_responses=True)

        self._worker_type: WorkerType = worker_type

        if worker_type == "llm":
            self._stream = settings.redis_llm_stream
            self._group = settings.redis_llm_group
            self._consumer = settings.redis_llm_consumer
        elif worker_type == "test_runner":
            self._stream = settings.redis_test_run_stream
            self._group = settings.redis_test_group
            self._consumer = settings.redis_test_consumer
        else:
            raise ValueError(f"Unknown worker_type: {worker_type}")

        self._ensure_group()

    @classmethod
    def llm(cls, redis_url: str | None = None) -> "RedisConsumer":
        return cls(worker_type="llm", redis_url=redis_url)

    @classmethod
    def test_runner(cls, redis_url: str | None = None) -> "RedisConsumer":
        return cls(worker_type="test_runner", redis_url=redis_url)

    def _ensure_group(self) -> None:
        try:
            self._r.xgroup_create(self._stream, self._group, id="0", mkstream=True)
        except redis.ResponseError as e:
            # group already exists
            if "BUSYGROUP" not in str(e):
                raise

    def consume(
        self,
        handler: Callable[[bytes], None],
        *,
        block_ms: int = 5000,
        count: int = 1,
        on_error_sleep_s: float = 1.0,
    ) -> None:
        """
        handler(body: bytes) -> None
        """
        while True:
            resp = self._r.xreadgroup(
                groupname=self._group,
                consumername=self._consumer,
                streams={self._stream: ">"},
                count=count,
                block=block_ms,
            )
            if not resp:
                continue

            _, messages = resp[0]  # type: ignore[index]
            for msg_id, fields in messages:
                try:
                    body = json.dumps(fields).encode("utf-8")
                    handler(body)
                    self._r.xack(self._stream, self._group, msg_id)
                except Exception:
                    time.sleep(on_error_sleep_s)

    def consume_llm(
        self,
        handler: Callable[[bytes], None],
        *,
        block_ms: int = 5000,
        count: int = 1,
        on_error_sleep_s: float = 1.0,
    ) -> None:
        if self._worker_type != "llm":
            raise RuntimeError("This consumer instance is not configured for LLM")
        self.consume(handler, block_ms=block_ms, count=count, on_error_sleep_s=on_error_sleep_s)

    def consume_test_runner(
        self,
        handler: Callable[[bytes], None],
        *,
        block_ms: int = 5000,
        count: int = 1,
        on_error_sleep_s: float = 1.0,
    ) -> None:
        if self._worker_type != "test_runner":
            raise RuntimeError("This consumer instance is not configured for Test Runner")
        self.consume(handler, block_ms=block_ms, count=count, on_error_sleep_s=on_error_sleep_s)

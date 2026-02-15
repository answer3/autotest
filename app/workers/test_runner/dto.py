import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, Playwright

import app.workers.test_runner.patterns as runner_patterns
from app.exceptions import PlanExecutionError
from app.models.enums import TestRunStatus
from app.workers.test_runner.validators import _validate_line_no_double_slash_regex


@dataclass(frozen=True)
class RunTestOutput:
    status: TestRunStatus
    final_url: str
    executed_steps: list[str]
    executed_assertions: list[str]
    timeout_ms: float
    browser: str
    headless: bool
    video_name: str | None = None
    screenshot_name: str | None = None


@dataclass
class PlanExecutionFailed(Exception):
    result: Any  # RunTestOutput
    original_exc: Exception

    def __str__(self) -> str:
        return str(self.original_exc)


@dataclass
class PlaywrightSession:
    playwright: Playwright
    browser: Browser
    context: BrowserContext
    page: Page


@dataclass
class SessionArtifacts:
    video_name: str | None = None
    screenshot_name: str | None = None


@dataclass(frozen=True)
class PlaywrightRunnerConfig:
    headless: bool
    timeout_ms: float
    browser_name: str
    artifacts_root: Path

    video_size: tuple[int, int] = (1280, 720)


@dataclass(frozen=True)
class PlanPayload:
    steps: list[str]
    assertions: list[str]

    @classmethod
    def from_any(cls, raw: Any) -> "PlanPayload":
        if raw is None:
            raise PlanExecutionError("plan_payload is null")

        if isinstance(raw, str):
            raw = json.loads(raw)

        if not isinstance(raw, dict):
            raise PlanExecutionError("plan_payload must be a dict or json-string")

        extra_keys = set(raw.keys()) - {"steps", "assertions"}
        if extra_keys:
            raise PlanExecutionError(f"unexpected keys in plan_payload: {sorted(extra_keys)}")

        steps = raw.get("steps") or []
        assertions = raw.get("assertions") or []

        if not isinstance(steps, list) or not all(isinstance(x, str) for x in steps):
            raise PlanExecutionError("plan_payload.steps must be list[str]")
        if not isinstance(assertions, list) or not all(isinstance(x, str) for x in assertions):
            raise PlanExecutionError("plan_payload.assertions must be list[str]")

        if not any(runner_patterns.RE_GOTO.match(s.strip()) for s in steps):
            raise PlanExecutionError("steps must include at least one page.goto(...)")

        for s in steps:
            _validate_line_no_double_slash_regex(s)
        for a in assertions:
            _validate_line_no_double_slash_regex(a)

        return cls(steps=[s.strip() for s in steps], assertions=[a.strip() for a in assertions])

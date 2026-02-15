import re
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from playwright.async_api import Page, Playwright, async_playwright, expect

import app.workers.test_runner.patterns as runner_patterns
from app.exceptions import PlanExecutionError
from app.models.enums import TestRunStatus
from app.workers.test_runner.artifacts import ensure_dir, run_screenshot_dir, run_video_dir
from app.workers.test_runner.dto import (
    PlanExecutionFailed,
    PlanPayload,
    PlaywrightRunnerConfig,
    PlaywrightSession,
    RunTestOutput,
    SessionArtifacts,
)


class PlaywrightSessionFactory:
    def __init__(self, cfg: PlaywrightRunnerConfig) -> None:
        self._cfg = cfg

    @property
    def browser_name(self) -> str:
        return self._cfg.browser_name

    @property
    def headless(self) -> bool:
        return self._cfg.headless

    @property
    def timeout_ms(self) -> float:
        return self._cfg.timeout_ms

    @property
    def artifacts_root(self) -> Path | None:
        return self._cfg.artifacts_root

    async def make_screenshot(self, *, page: Page, run_id: int) -> str | None:
        if not self.artifacts_root:
            return None
        try:
            screenshots_dir = ensure_dir(run_screenshot_dir(self.artifacts_root, run_id))
            filename = f"{uuid.uuid4()}.png"
            full_path = screenshots_dir / filename

            await page.screenshot(
                path=str(full_path),
                full_page=True,
            )
            return filename
        except Exception:
            return None

    def _get_browser_launcher(self, p: Playwright) -> Any:
        launcher = getattr(p, self._cfg.browser_name, None)
        if launcher is None:
            raise PlanExecutionError(f"Unsupported browser: {self._cfg.browser_name}")
        return launcher

    @asynccontextmanager
    async def session(
        self,
        *,
        base_url: str,
        run_id: int,
    ) -> AsyncIterator[tuple[PlaywrightSession, SessionArtifacts]]:
        async with async_playwright() as p:
            launcher = self._get_browser_launcher(p)
            browser = await launcher.launch(headless=self._cfg.headless)

            context_kwargs: dict[str, Any] = {"base_url": base_url}

            if self._cfg.artifacts_root:
                video_dir = ensure_dir(run_video_dir(self._cfg.artifacts_root, run_id))
                context_kwargs["record_video_dir"] = str(video_dir)
                context_kwargs["record_video_size"] = {
                    "width": self._cfg.video_size[0],
                    "height": self._cfg.video_size[1],
                }

            context = await browser.new_context(**context_kwargs)
            page = await context.new_page()
            page.set_default_timeout(self._cfg.timeout_ms)

            artifacts = SessionArtifacts()
            session = PlaywrightSession(playwright=p, browser=browser, context=context, page=page)

            try:
                yield session, artifacts
            finally:
                video = page.video

                try:
                    await page.close()
                finally:
                    if video is not None:
                        try:
                            artifacts.video_name = Path(await video.path()).name
                        except Exception:
                            artifacts.video_name = None

                    await context.close()
                    await browser.close()


class PlaywrightRunner:
    def __init__(self, session_factory: PlaywrightSessionFactory) -> None:
        self._sf = session_factory

    async def _run_step(self, step: str, page: Any) -> str | None:
        s = step.strip()

        m = runner_patterns.RE_GOTO.match(s)
        if m:
            await page.goto(m.group("url"))
            return s

        m = runner_patterns.RE_FILL.match(s)
        if m:
            await page.fill(m.group("sel"), m.group("val"))
            return "await page.fill('<***>', '<***>')"

        m = runner_patterns.RE_CLICK.match(s)
        if m:
            await page.click(m.group("sel"))
            return s

        m = runner_patterns.RE_WAIT_SEL.match(s)
        if m:
            await page.wait_for_selector(m.group("sel"))
            return s

        m = runner_patterns.RE_WAIT_URL_STR.match(s)
        if m:
            await page.wait_for_url(m.group("url"))
            return s

        m = runner_patterns.RE_WAIT_URL_RE.match(s)
        if m:
            await page.wait_for_url(re.compile(m.group("pat")))
            return s

        return None

    async def _run_assertion(self, assertion: str, page: Any) -> str | None:
        a = assertion.strip()

        m = runner_patterns.RE_EXPECT_URL_STR.match(a)
        if m:
            await expect(page).to_have_url(m.group("url"))
            return a

        m = runner_patterns.RE_EXPECT_URL_RE.match(a)
        if m:
            await expect(page).to_have_url(re.compile(m.group("pat")))
            return a

        m = runner_patterns.RE_EXPECT_VISIBLE.match(a)
        if m:
            await expect(page.locator(m.group("sel"))).to_be_visible()
            return a

        m = runner_patterns.RE_EXPECT_CONTAINS.match(a)
        if m:
            await expect(page.locator(m.group("sel"))).to_contain_text(m.group("text"))
            return a

        return None

    async def execute_plan(self, plan: PlanPayload, *, base_url: str, run_id: int) -> RunTestOutput:
        executed_steps: list[str] = []
        executed_assertions: list[str] = []
        final_url: str = ""

        async with self._sf.session(base_url=base_url, run_id=run_id) as (s, artifacts):
            page = s.page

            try:
                for i, raw in enumerate(plan.steps, start=1):
                    executed_step = await self._run_step(raw, page)
                    if not executed_step:
                        raise PlanExecutionError(f"Unsupported step #{i}: {raw}")
                    executed_steps.append(executed_step)

                for i, raw in enumerate(plan.assertions, start=1):
                    executed_assertion = await self._run_assertion(raw, page)
                    if not executed_assertion:
                        raise PlanExecutionError(f"Unsupported assertion #{i}: {raw}")
                    executed_assertions.append(executed_assertion)

                final_url = page.url

            except Exception as e:
                try:
                    artifacts.screenshot_name = await self._sf.make_screenshot(
                        page=page, run_id=run_id
                    )
                except Exception:
                    artifacts.screenshot_name = None

                try:
                    final_url = page.url
                except Exception:
                    final_url = ""

                failed = RunTestOutput(
                    status=TestRunStatus.failed,
                    final_url=final_url,
                    executed_steps=executed_steps,
                    executed_assertions=executed_assertions,
                    timeout_ms=self._sf.timeout_ms,
                    browser=self._sf.browser_name,
                    headless=self._sf.headless,
                    video_name=artifacts.video_name,
                    screenshot_name=artifacts.screenshot_name,
                )
                raise PlanExecutionFailed(result=failed, original_exc=e) from e

        return RunTestOutput(
            status=TestRunStatus.passed,
            final_url=final_url,
            executed_steps=executed_steps,
            executed_assertions=executed_assertions,
            timeout_ms=self._sf.timeout_ms,
            browser=self._sf.browser_name,
            headless=self._sf.headless,
            video_name=artifacts.video_name,
            screenshot_name=None,
        )

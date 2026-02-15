import re
from unittest.mock import AsyncMock, Mock

import pytest

import app.workers.test_runner.playwright_run as runner_mod
from app.models.enums import TestRunStatus
from app.workers.test_runner.dto import PlanExecutionFailed, PlanPayload
from app.workers.test_runner.playwright_run import PlaywrightRunner
from tests.conftest import FakeExpectPlaywright, FakeSessionFactory, make_page


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "step, method, args, expected_return",
    [
        (
                "await page.goto('https://x')",
                "goto",
                ("https://x",),
                "await page.goto('https://x')",
        ),
        (
                "await page.click('#btn')",
                "click",
                ("#btn",),
                "await page.click('#btn')",
        ),
        (
                "await page.waitForSelector('#x')",
                "wait_for_selector",
                ("#x",),
                "await page.waitForSelector('#x')",
        ),
        (
                "await page.waitForURL('https://x')",
                "wait_for_url",
                ("https://x",),
                "await page.waitForURL('https://x')",
        ),
        (
                "await page.fill('#email', 'a@b.com')",
                "fill",
                ("#email", "a@b.com"),
                "await page.fill('<***>', '<***>')",
        ),
    ],
)
async def test_run_step_dispatch(step, method, args, expected_return):
    runner = PlaywrightRunner(session_factory=Mock())
    page = AsyncMock()

    res = await runner._run_step(step, page)

    assert res == expected_return
    getattr(page, method).assert_awaited_once_with(*args)


@pytest.mark.asyncio
async def test_run_step_wait_url_regex_compiles_pattern():
    runner = PlaywrightRunner(session_factory=Mock())
    page = AsyncMock()

    step = r"await page.waitForURL(/secure.*/)"
    res = await runner._run_step(step, page)

    assert res == step

    assert page.wait_for_url.await_count == 1
    (arg0,), _kwargs = page.wait_for_url.await_args
    assert isinstance(arg0, re.Pattern)
    assert arg0.pattern == "secure.*"


@pytest.mark.asyncio
async def test_run_step_unsupported_returns_none():
    runner = PlaywrightRunner(session_factory=Mock())
    page = AsyncMock()

    res = await runner._run_step("await page.type('#x', 'y')", page)
    assert res is None


# ------------------------------
# Assertions: monkeypatch expect
# ------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "assertion, expected_kind, expected_value",
    [
        (
                "await expect(page).toHaveURL('https://x')",
                "to_have_url",
                "https://x",
        ),
        (
                r"await expect(page).toHaveURL(/secure.*/)",
                "to_have_url",
                re.compile("secure.*"),
        ),
        (
                "await expect(page.locator('#x')).toBeVisible()",
                "to_be_visible",
                None,
        ),
        (
                "await expect(page.locator('#x')).toContainText('Hello')",
                "to_contain_text",
                "Hello",
        ),
    ],
)
async def test_run_assertion_dispatch(monkeypatch, assertion, expected_kind, expected_value):
    runner = PlaywrightRunner(session_factory=Mock())

    page = AsyncMock()
    locator_obj = object()
    page.locator = Mock(return_value=locator_obj)
    fake_expect = FakeExpectPlaywright(page, locator_obj)
    monkeypatch.setattr(runner_mod, "expect", fake_expect, raising=True)

    res = await runner._run_assertion(assertion, page)
    assert res == assertion

    if expected_kind == "to_have_url" and isinstance(expected_value, re.Pattern):
        assert fake_expect.page_matcher.calls[0][0] == "to_have_url"
        arg = fake_expect.page_matcher.calls[0][1]
        assert isinstance(arg, re.Pattern)
        assert arg.pattern == expected_value.pattern
    elif expected_kind == "to_have_url":
        assert fake_expect.page_matcher.calls == [("to_have_url", expected_value)]
    elif expected_kind == "to_be_visible":
        page.locator.assert_called_once_with("#x")
        assert fake_expect.locator_matcher.calls == [("to_be_visible", None)]
    elif expected_kind == "to_contain_text":
        page.locator.assert_called_once_with("#x")
        assert fake_expect.locator_matcher.calls == [("to_contain_text", expected_value)]
    else:
        raise AssertionError("Unexpected expected_kind")


@pytest.mark.asyncio
async def test_run_assertion_unsupported_returns_none(monkeypatch):
    runner = PlaywrightRunner(session_factory=Mock())

    page = AsyncMock()
    locator_obj = object()
    page.locator = AsyncMock(return_value=locator_obj)

    fake_expect = FakeExpectPlaywright(page, locator_obj)
    monkeypatch.setattr(runner_mod, "expect", fake_expect, raising=True)

    res = await runner._run_assertion("await expect(page).toHaveTitle('X')", page)
    assert res is None


@pytest.mark.asyncio
async def test_execute_plan_step_runtime_error_raises_plan_execution_failed_and_keeps_executed_steps():
    page = make_page(url="https://example.com/fail")

    # make click raise during execution
    async def _boom(*args, **kwargs):
        raise RuntimeError("click failed")

    page.click.side_effect = _boom

    sf = FakeSessionFactory(page, screenshot_name="shot.png", video_name="vid.webm")
    runner = PlaywrightRunner(sf)

    plan = PlanPayload(
        steps=[
            "await page.goto('https://x')",
            "await page.click('#btn')",  # raises
            "await page.waitForSelector('#x')",
        ],
        assertions=[],
    )

    with pytest.raises(PlanExecutionFailed) as ei:
        await runner.execute_plan(plan, base_url="https://base", run_id=11)

    e = ei.value
    assert e.result.status == TestRunStatus.failed
    assert e.result.final_url == "https://example.com/fail"
    assert e.result.executed_steps == ["await page.goto('https://x')"]
    assert e.result.screenshot_name == "shot.png"


@pytest.mark.asyncio
async def test_execute_plan_when_page_url_raises_sets_final_url_empty_string():
    page = make_page(url_raises=True)

    # also force failure
    async def _boom(*args, **kwargs):
        raise RuntimeError("goto failed")

    page.goto.side_effect = _boom

    sf = FakeSessionFactory(page, screenshot_name="shot.png", video_name="vid.webm")
    runner = PlaywrightRunner(sf)

    plan = PlanPayload(
        steps=["await page.goto('https://x')"],
        assertions=[],
    )

    with pytest.raises(PlanExecutionFailed) as ei:
        await runner.execute_plan(plan, base_url="https://base", run_id=12)

    e = ei.value
    assert e.result.status == TestRunStatus.failed
    assert e.result.final_url == ""
    assert e.result.screenshot_name == "shot.png"


@pytest.mark.asyncio
async def test_execute_plan_when_make_screenshot_fails_keeps_screenshot_name_none():
    page = make_page(url="https://example.com/fail")

    async def _boom(*args, **kwargs):
        raise RuntimeError("goto failed")

    page.goto.side_effect = _boom

    sf = FakeSessionFactory(page, make_screenshot_raises=True, video_name="vid.webm")
    runner = PlaywrightRunner(sf)

    plan = PlanPayload(steps=["await page.goto('https://x')"], assertions=[])

    with pytest.raises(PlanExecutionFailed) as ei:
        await runner.execute_plan(plan, base_url="https://base", run_id=13)

    e = ei.value
    assert e.result.status == TestRunStatus.failed
    assert e.result.screenshot_name is None
    assert e.result.video_name == "vid.webm"

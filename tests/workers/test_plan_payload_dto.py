import json

import pytest

from app.workers.test_runner.dto import PlanExecutionError, PlanPayload
from tests.data.data_plan_payload_dto import (
    PLAN_BAD_ASSERT_ELEM_TYPE,
    PLAN_BAD_ASSERT_TYPE,
    PLAN_BAD_STEP_ELEM_TYPE,
    PLAN_BAD_STEPS_TYPE,
    PLAN_EXTRA_KEYS,
    PLAN_HAS_DOUBLE_SLASH_REGEX_IN_ASSERT,
    PLAN_HAS_DOUBLE_SLASH_REGEX_IN_STEP,
    PLAN_MIN_OK,
    PLAN_NO_GOTO,
    PLAN_OK_WITH_SPACES,
)

# -----------------------------
# Valid
# -----------------------------

@pytest.mark.parametrize(
    "raw",
    [
        PLAN_MIN_OK,
        json.dumps(PLAN_MIN_OK),
    ],
)
def test_plan_payload_from_any_ok(raw):
    p = PlanPayload.from_any(raw)
    assert p.steps == ["await page.goto('https://example.com')"]
    assert p.assertions == []


def test_plan_payload_from_any_strips_spaces():
    p = PlanPayload.from_any(PLAN_OK_WITH_SPACES)
    assert p.steps == [
        "await page.goto('https://example.com')",
        "await page.click('#x')",
    ]
    assert p.assertions == [
        "await expect(page.locator('#x')).toBeVisible()"
    ]


# -----------------------------
# Basic input errors
# -----------------------------

@pytest.mark.parametrize(
    "raw, match",
    [
        (None, r"plan_payload is null"),
        (123, r"plan_payload must be a dict or json-string"),
        (["x"], r"plan_payload must be a dict or json-string"),
    ],
)
def test_plan_payload_from_any_basic_errors(raw, match):
    with pytest.raises(PlanExecutionError, match=match):
        PlanPayload.from_any(raw)


def test_plan_payload_from_any_invalid_json_string():
    with pytest.raises(ValueError):  # json.JSONDecodeError наследник ValueError
        PlanPayload.from_any("{not-json}")


def test_plan_payload_from_any_extra_keys_raises():
    with pytest.raises(PlanExecutionError, match=r"unexpected keys in plan_payload"):
        PlanPayload.from_any(PLAN_EXTRA_KEYS)


# -----------------------------
# Type validation
# -----------------------------

@pytest.mark.parametrize(
    "raw, match",
    [
        (PLAN_BAD_STEPS_TYPE, r"plan_payload\.steps must be list\[str\]"),
        (PLAN_BAD_STEP_ELEM_TYPE, r"plan_payload\.steps must be list\[str\]"),
        (PLAN_BAD_ASSERT_TYPE, r"plan_payload\.assertions must be list\[str\]"),
        (PLAN_BAD_ASSERT_ELEM_TYPE, r"plan_payload\.assertions must be list\[str\]"),
    ],
)
def test_plan_payload_from_any_type_errors(raw, match):
    with pytest.raises(PlanExecutionError, match=match):
        PlanPayload.from_any(raw)


# -----------------------------
# Semantic rules
# -----------------------------

def test_plan_payload_from_any_requires_goto():
    with pytest.raises(PlanExecutionError, match=r"steps must include at least one page\.goto"):
        PlanPayload.from_any(PLAN_NO_GOTO)


@pytest.mark.parametrize(
    "raw",
    [
        PLAN_HAS_DOUBLE_SLASH_REGEX_IN_STEP,
        PLAN_HAS_DOUBLE_SLASH_REGEX_IN_ASSERT,
    ],
)
def test_plan_payload_from_any_rejects_double_slash_regex(raw):
    with pytest.raises(
        PlanExecutionError,
        match=r"Invalid regex delimiter //\.\.\.// in:",
    ):
        PlanPayload.from_any(raw)

import copy
import json

import pytest

from app.llm.llm_output_validator import PlanValidationError, validate_plan_payload
from tests.data.data_plan_validator import (
    PLAN_BAD_ASSERTION,
    PLAN_BAD_STEP,
    PLAN_BAD_TYPES_1,
    PLAN_BAD_TYPES_2,
    PLAN_BAD_TYPES_3,
    PLAN_BAD_TYPES_4,
    PLAN_EXTRA_KEYS,
    PLAN_MIN_OK,
    PLAN_NO_GOTO,
    PLAN_OK,
    PLAN_WITH_SPACES,
)

# ---------------------------
# Valid payloads
# ---------------------------

@pytest.mark.parametrize(
    "raw, expected_steps, expected_assertions",
    [
        (PLAN_OK, PLAN_OK["steps"], PLAN_OK["assertions"]),
        (PLAN_MIN_OK, PLAN_MIN_OK["steps"], PLAN_MIN_OK["assertions"]),
        (
                PLAN_WITH_SPACES,
                ["await page.goto('https://example.com')", "await page.click('#btn')"],
                ["await expect(page.locator('#x')).toBeVisible()"],
        ),
        (json.dumps(PLAN_OK), PLAN_OK["steps"], PLAN_OK["assertions"]),
    ],
)
def test_validate_plan_payload_ok(raw, expected_steps, expected_assertions):
    out = validate_plan_payload(raw)
    assert out["steps"] == expected_steps
    assert out["assertions"] == expected_assertions


# ---------------------------
# Basic input errors
# ---------------------------

@pytest.mark.parametrize(
    "raw, match",
    [
        (None, r"plan_payload is null"),
        ("{not-json}", r"plan_payload is not valid JSON"),
        (["steps"], r"plan_payload must be a JSON object"),
        (PLAN_EXTRA_KEYS, r"unexpected keys in plan_payload"),
    ],
)
def test_validate_plan_payload_basic_errors(raw, match):
    with pytest.raises(PlanValidationError, match=match):
        validate_plan_payload(raw)


# ---------------------------
# Type validation
# ---------------------------

@pytest.mark.parametrize(
    "raw, match",
    [
        (PLAN_BAD_TYPES_1, r"steps must be list\[str\]"),
        (PLAN_BAD_TYPES_2, r"steps must be list\[str\]"),
        (PLAN_BAD_TYPES_3, r"assertions must be list\[str\]"),
        (PLAN_BAD_TYPES_4, r"assertions must be list\[str\]"),
    ],
)
def test_validate_plan_payload_type_errors(raw, match):
    with pytest.raises(PlanValidationError, match=match):
        validate_plan_payload(raw)


# ---------------------------
# Semantic rules
# ---------------------------

@pytest.mark.parametrize(
    "raw, match",
    [
        (PLAN_NO_GOTO, r"steps must include at least one page\.goto"),
        (PLAN_BAD_STEP, r"unsupported step #2:"),
        (PLAN_BAD_ASSERTION, r"unsupported assertion #1:"),
    ],
)
def test_validate_plan_payload_semantic_errors(raw, match):
    with pytest.raises(PlanValidationError, match=match):
        validate_plan_payload(raw)


# ---------------------------
# Limits
# ---------------------------

@pytest.mark.parametrize(
    "steps_n, max_steps, match",
    [
        (61, 60, r"too many steps: 61 > 60"),
        (3, 2, r"too many steps: 3 > 2"),
    ],
)
def test_validate_plan_payload_steps_limit(steps_n, max_steps, match):
    raw = {"steps": PLAN_MIN_OK["steps"] * steps_n, "assertions": []}
    with pytest.raises(PlanValidationError, match=match):
        validate_plan_payload(raw, max_steps=max_steps)


@pytest.mark.parametrize(
    "assertions_n, max_assertions, match",
    [
        (41, 40, r"too many assertions: 41 > 40"),
        (2, 1, r"too many assertions: 2 > 1"),
    ],
)
def test_validate_plan_payload_assertions_limit(assertions_n, max_assertions, match):
    raw = {
        "steps": PLAN_MIN_OK["steps"],
        "assertions": ["await expect(page.locator('#x')).toBeVisible()"] * assertions_n,
    }
    with pytest.raises(PlanValidationError, match=match):
        validate_plan_payload(raw, max_assertions=max_assertions)


# ---------------------------
# Output normalization (strip)
# ---------------------------

def test_validate_plan_payload_returns_only_steps_and_assertions():
    raw = copy.deepcopy(PLAN_OK)
    out = validate_plan_payload(raw)
    assert set(out.keys()) == {"steps", "assertions"}

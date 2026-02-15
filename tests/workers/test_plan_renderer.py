import json

import pytest

from app.workers.test_runner.renderer import (
    apply_placeholders,
    normalize_base_url,
    normalize_js_regex_url,
    render_plan,
)
from tests.data.data_renderer import (
    BASE_URL_BAD,
    BASE_URL_OK,
    JS_REGEX_NORMALIZE,
    PLACEHOLDERS_OK,
    PLAN_BAD_ASSERT_ELEM_TYPE,
    PLAN_BAD_ASSERT_TYPE,
    PLAN_BAD_STEP_ELEM_TYPE,
    PLAN_BAD_STEPS_TYPE,
    PLAN_OK,
    PLAN_RENDERED_OK,
    PLAN_WITH_UNRESOLVED,
    TEXT_WITH_PLACEHOLDERS,
    TEXT_WITH_UNRESOLVED,
)

# -----------------------------
# normalize_base_url
# -----------------------------

@pytest.mark.parametrize("raw, expected", BASE_URL_OK)
def test_normalize_base_url_ok(raw, expected):
    assert normalize_base_url(raw) == expected


@pytest.mark.parametrize("raw, match", BASE_URL_BAD)
def test_normalize_base_url_bad(raw, match):
    with pytest.raises(ValueError, match=match):
        normalize_base_url(raw)


# -----------------------------
# normalize_js_regex_url
# -----------------------------

@pytest.mark.parametrize("raw, expected", JS_REGEX_NORMALIZE)
def test_normalize_js_regex_url(raw, expected):
    assert normalize_js_regex_url(raw) == expected


# -----------------------------
# apply_placeholders
# -----------------------------

def test_apply_placeholders_ok():
    out = apply_placeholders(TEXT_WITH_PLACEHOLDERS, PLACEHOLDERS_OK)
    assert out == "await page.fill('#email', 'a@b.com')"


def test_apply_placeholders_unresolved_raises():
    with pytest.raises(ValueError, match="unresolved placeholders remain after substitution"):
        apply_placeholders(TEXT_WITH_UNRESOLVED, PLACEHOLDERS_OK)


# -----------------------------
# render_plan
# -----------------------------

@pytest.mark.parametrize(
    "raw, expected",
    [
        (PLAN_OK, PLAN_RENDERED_OK),
        (json.dumps(PLAN_OK), PLAN_RENDERED_OK),
    ],
)
def test_render_plan_ok(raw, expected):
    out = render_plan(raw, PLACEHOLDERS_OK)
    assert out == expected


@pytest.mark.parametrize(
    "raw, match",
    [
        ("not-json", "Expecting value|plan_payload must be dict or json-string"),  # json.loads может дать другое сообщение
        (123, "plan_payload must be dict or json-string"),
        (PLAN_BAD_STEPS_TYPE, "plan_payload\\.steps must be list\\[str\\]"),
        (PLAN_BAD_STEP_ELEM_TYPE, "plan_payload\\.steps must be list\\[str\\]"),
        (PLAN_BAD_ASSERT_TYPE, "plan_payload\\.assertions must be list\\[str\\]"),
        (PLAN_BAD_ASSERT_ELEM_TYPE, "plan_payload\\.assertions must be list\\[str\\]"),
    ],
)
def test_render_plan_bad_input_raises(raw, match):
    with pytest.raises(ValueError, match=match):
        render_plan(raw, PLACEHOLDERS_OK)


def test_render_plan_unresolved_placeholder_raises():
    with pytest.raises(ValueError, match="unresolved placeholders remain after substitution"):
        render_plan(PLAN_WITH_UNRESOLVED, PLACEHOLDERS_OK)

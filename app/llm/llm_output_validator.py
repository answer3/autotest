import json
import re
from typing import Any


class PlanValidationError(ValueError):
    pass


# --- Allowed patterns (JS-like strings from LLM) ---
RE_GOTO = re.compile(r"^await page\.goto\('(?P<url>[^']+)'\)$")
RE_FILL = re.compile(r"^await page\.fill\('(?P<sel>[^']+)',\s*'(?P<val>.*)'\)$")
RE_CLICK = re.compile(r"^await page\.click\('(?P<sel>[^']+)'\)$")
RE_WAIT_SEL = re.compile(r"^await page\.waitForSelector\('(?P<sel>[^']+)'\)$")
RE_WAIT_URL_STR = re.compile(r"^await page\.waitForURL\('(?P<url>[^']+)'\)$")
RE_WAIT_URL_RE = re.compile(r"^await page\.waitForURL\(/(?P<pat>.+)/\)$")

RE_EXPECT_URL_STR = re.compile(r"^await expect\(page\)\.toHaveURL\('(?P<url>[^']+)'\)$")
RE_EXPECT_URL_RE = re.compile(r"^await expect\(page\)\.toHaveURL\(/(?P<pat>.+)/\)$")
RE_EXPECT_VISIBLE = re.compile(
    r"^await expect\(page\.locator\('(?P<sel>[^']+)'\)\)\.toBeVisible\(\)$"
)
RE_EXPECT_CONTAINS = re.compile(
    r"^await expect\(page\.locator\('(?P<sel>[^']+)'\)\)\.toContainText\('(?P<text>.*)'\)$"
)

ALLOWED_STEP_RES = [RE_GOTO, RE_FILL, RE_CLICK, RE_WAIT_SEL, RE_WAIT_URL_STR, RE_WAIT_URL_RE]
ALLOWED_ASSERT_RES = [RE_EXPECT_URL_STR, RE_EXPECT_URL_RE, RE_EXPECT_VISIBLE, RE_EXPECT_CONTAINS]


def validate_plan_payload(
    raw: Any, *, max_steps: int = 60, max_assertions: int = 40
) -> dict[str, Any]:
    if raw is None:
        raise PlanValidationError("plan_payload is null")

    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception as e:
            raise PlanValidationError(f"plan_payload is not valid JSON: {e}") from e

    if not isinstance(raw, dict):
        raise PlanValidationError("plan_payload must be a JSON object")

    # only allowed keys
    extra = set(raw.keys()) - {"steps", "assertions"}
    if extra:
        raise PlanValidationError(f"unexpected keys in plan_payload: {sorted(extra)}")

    steps = raw.get("steps")
    assertions = raw.get("assertions")

    if not isinstance(steps, list) or not all(isinstance(x, str) for x in steps):
        raise PlanValidationError("steps must be list[str]")
    if not isinstance(assertions, list) or not all(isinstance(x, str) for x in assertions):
        raise PlanValidationError("assertions must be list[str]")

    if len(steps) > max_steps:
        raise PlanValidationError(f"too many steps: {len(steps)} > {max_steps}")
    if len(assertions) > max_assertions:
        raise PlanValidationError(f"too many assertions: {len(assertions)} > {max_assertions}")

    # validate each line
    def _match_any(string: str, res: list[re.Pattern[str]]) -> bool:
        return any(r.match(string.strip()) for r in res)

    for i, s in enumerate(steps, 1):
        if not _match_any(s, ALLOWED_STEP_RES):
            raise PlanValidationError(f"unsupported step #{i}: {s}")

    for i, a in enumerate(assertions, 1):
        if not _match_any(a, ALLOWED_ASSERT_RES):
            raise PlanValidationError(f"unsupported assertion #{i}: {a}")

    # simple semantics: must have goto
    if not any(RE_GOTO.match(s.strip()) for s in steps):
        raise PlanValidationError("steps must include at least one page.goto(...)")

    return {"steps": [s.strip() for s in steps], "assertions": [a.strip() for a in assertions]}

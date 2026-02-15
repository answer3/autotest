import json
import re
from typing import Any
from urllib.parse import urlparse

import app.workers.test_runner.patterns as runner_patterns


def normalize_base_url(site_domain: str) -> str:
    site_domain = (site_domain or "").strip()
    if not site_domain:
        raise ValueError("site_domain is empty")

    u = urlparse(site_domain)
    if u.scheme not in ("http", "https"):
        raise ValueError("site_domain must include http/https scheme, e.g. https://example.com")
    if not u.netloc:
        raise ValueError("site_domain netloc is empty")
    if u.path not in ("", "/") or u.query or u.fragment:
        raise ValueError("site_domain must not include path/query/fragment")

    return f"{u.scheme}://{u.netloc}"


def normalize_js_regex_url(s: str) -> str:
    s = re.sub(r"waitForURL\(\s*//(.+?)//\s*\)", r"waitForURL(/\1/)", s)
    s = re.sub(r"toHaveURL\(\s*//(.+?)//\s*\)", r"toHaveURL(/\1/)", s)
    return s


def _safe_placeholder_keys(placeholders: dict[str, str]) -> list[str]:
    return list(placeholders.keys())


def apply_placeholders(text: str, placeholders: dict[str, str]) -> str:
    for k, v in placeholders.items():
        text = text.replace(k, v)

    if runner_patterns.PLACEHOLDER_RE.search(text):
        raise ValueError("unresolved placeholders remain after substitution")
    return text


def parse_placeholders(placeholders_raw: Any) -> dict[str, Any]:
    if placeholders_raw is None:
        return {}

    if isinstance(placeholders_raw, str):
        try:
            placeholders = json.loads(placeholders_raw)
        except Exception:
            return {}
    else:
        placeholders = placeholders_raw

    if not isinstance(placeholders, dict):
        return {}

    out: dict[str, str] = {}
    for k, v in placeholders.items():
        if isinstance(k, str) and isinstance(v, str):
            out[k] = v
        else:
            return {}

    return out


def render_plan(plan_payload: Any, placeholders: dict[str, str]) -> dict[str, Any]:
    if isinstance(plan_payload, str):
        plan_payload = json.loads(plan_payload)

    if not isinstance(plan_payload, dict):
        raise ValueError("plan_payload must be dict or json-string")

    steps = plan_payload.get("steps") or []
    assertions = plan_payload.get("assertions") or []

    if not isinstance(steps, list) or not all(isinstance(x, str) for x in steps):
        raise ValueError("plan_payload.steps must be list[str]")
    if not isinstance(assertions, list) or not all(isinstance(x, str) for x in assertions):
        raise ValueError("plan_payload.assertions must be list[str]")

    steps2 = []
    for s in steps:
        s = apply_placeholders(s, placeholders)
        s = normalize_js_regex_url(s)
        steps2.append(s)

    assertions2 = []
    for a in assertions:
        a = apply_placeholders(a, placeholders)
        a = normalize_js_regex_url(a)
        assertions2.append(a)
    return {"steps": steps2, "assertions": assertions2}

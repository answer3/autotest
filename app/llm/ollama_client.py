import json
import re
from typing import Any, Protocol

import requests

from app.core.config import settings
from app.llm.llm_output_validator import validate_plan_payload
from app.llm.utils import get_llm_request_payload


def _extract_json_object(text: str) -> str:
    text = text.strip()

    m = re.search(r"```json\s*(\{[\s\S]*?})\s*```", text)
    if m:
        return m.group(1).strip()

    # fallback: first {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    raise ValueError("No JSON object found in LLM response")


class LLMClient(Protocol):
    def generate_plan_json(self, nl_text: str) -> dict[str, Any]: ...


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self._base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self._model = model or settings.ollama_model

    def generate_plan_json(self, nl_text: str) -> dict[str, Any]:
        payload = get_llm_request_payload(
            nl_text, self._model, settings.num_predict, settings.num_ctx
        )

        r = requests.post(f"{self._base_url}/api/generate", json=payload, timeout=600)
        r.raise_for_status()

        data = r.json()
        if data.get("done_reason") == "length":
            raise RuntimeError(
                f"ollama_error: truncated output (done_reason=length). Increase num_predict. Partial: {data.get('response', '')[:200]!r}"
            )

        raw = (data.get("response") or "").strip()

        try:
            plan_json = json.loads(raw)
        except json.JSONDecodeError:
            json_text = _extract_json_object(raw)
            plan_json = json.loads(json_text)

        valid_plan = validate_plan_payload(plan_json)

        return valid_plan

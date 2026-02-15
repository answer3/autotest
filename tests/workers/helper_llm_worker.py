import json

from tests.data.data_llm_worker import LLM_PAYLOAD_OK


def msg(proposal_id: int) -> bytes:
    return json.dumps({"proposal_id": proposal_id}).encode("utf-8")


class OllamaOK:
    def __init__(self):
        self._payload = LLM_PAYLOAD_OK

    def generate_plan_json(self, nl_text: str):
        return self._payload


class OllamaBoom:
    def generate_plan_json(self, nl_text: str):
        raise RuntimeError("boom")

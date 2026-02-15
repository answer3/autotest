from typing import Any


def get_promt(nl_text: str) -> str:
    return (
        "You are a Playwright test generator.\n"
        "Target language: Python Playwright (async).\n"
        "Return ONLY valid JSON. No markdown. No explanations.\n\n"
        "Output schema (JSON only):\n"
        "{"
        '"steps": ["..."],'
        '"assertions": ["..."]'
        "}\n\n"
        "STRICT RULES:\n"
        "- EVERY statement MUST start with 'await'.\n"
        "- Use ONLY the commands listed below. No variations.\n"
        "- Use single quotes ' for all string literals.\n"
        "- Do NOT add comments or extra keys.\n"
        "- Do NOT invent selectors or roles. Use only selectors mentioned or clearly implied in NL_TEST_CASE.\n"
        "- Prefer explicit waits (waitForSelector, waitForURL) over implicit timing.\n"
        "- When a value is secret/user-provided, use placeholders like <login>, <password> instead of real values.\n\n"
        " - BASE_URL IMPORTANT: page.goto() MUST use ONLY relative paths like '/login'. Never output 'http://' or 'https://'.\n"
        " - Regex URLs MUST be written as /pattern/ (single leading/trailing slash). Never use //pattern//.\n"
        "ALLOWED STEPS:\n"
        "- await page.goto('<url>')\n"
        "- await page.fill('<selector>', '<value>')\n"
        "- await page.click('<selector>')\n"
        "- await page.waitForSelector('<selector>')\n"
        "- await page.waitForURL('<url>')\n"
        "- await page.waitForURL(/<regex>/)\n\n"
        "ALLOWED ASSERTIONS:\n"
        "- await expect(page).toHaveURL('<url>')\n"
        "- await expect(page).toHaveURL(/<regex>/)\n"
        "- await expect(page.locator('<selector>')).toBeVisible()\n"
        "- await expect(page.locator('<selector>')).toContainText('<text>')\n\n"
        "FORBIDDEN:\n"
        "- page.url()\n"
        "- isVisible(), isHidden(), isEnabled(), boolean checks\n"
        "- waitForTimeout(), sleep(), timeouts\n"
        "- evaluate(), eval(), $$eval()\n"
        "- locator().click(), locator().fill()\n"
        "- Any JavaScript code or Python code outside the allowed commands\n\n"
        "REQUIREMENTS:\n"
        "- steps MUST contain at least one page.goto(...).\n"
        "- assertions MUST validate the final state of the page.\n"
        "- Keep steps minimal and deterministic.\n\n"
        f"NL_TEST_CASE:\n{nl_text}\n"
    )


def get_llm_request_payload(nl_text: str, model: str, num_predict: int) -> dict[str, Any]:
    return {
        "model": model,
        "prompt": get_promt(nl_text),
        "stream": False,
        "format": "json",
        "options": {"num_predict": num_predict},
    }

from typing import Any


def get_promt(nl_text: str) -> str:
    return (
        "You are a Playwright test generator.\n"
        "Target language: Python Playwright (async).\n"
        "Return ONLY a single JSON object. No markdown. No explanations. No extra text.\n\n"
        "JSON schema (MUST match exactly; no extra keys):\n"
        "{"
        '"steps": ["..."],'
        '"assertions": ["..."]'
        "}\n\n"
        "STRICT OUTPUT RULES:\n"
        "- Output MUST be valid JSON and MUST start with '{' and end with '}'.\n"
        "- Use double quotes for JSON keys/strings. (JSON standard)\n"
        "- The values inside steps/assertions are Playwright statements and MUST use single quotes ' for their string literals.\n"
        "- Do NOT include comments, trailing commas, markdown fences, or any other keys.\n\n"
        "PLAYWRIGHT STATEMENT RULES:\n"
        "- EVERY statement MUST start with 'await '.\n"
        "- Use ONLY the commands listed below. No variations.\n"
        "- Do NOT output any Python code outside these statements.\n\n"
        "SELECTOR POLICY (IMPORTANT):\n"
        "- If a selector is explicitly provided in NL_TEST_CASE, use it as-is.\n"
        '- If a selector is clearly implied as an id/name/data-testid (e.g. "id=login" or "data-testid=submit"), '
        "use CSS selectors: '#id', '[name=\"...\"]', or '[data-testid=\"...\"]'.\n"
        "- Otherwise, DO NOT invent selectors. Use a placeholder selector in the form '<selector:meaningful_name>'.\n"
        "  Example: await page.click('<selector:submit_button>')\n"
        "- For placeholder values (credentials/secrets), use '<login>', '<password>', '<email>', etc.\n\n"
        "BASE_URL RULES:\n"
        "- page.goto() and URL assertions MUST use ONLY relative paths like '/login' or '/dashboard'.\n"
        "- Never output 'http://' or 'https://'.\n"
        "- waitForURL / toHaveURL may use either a relative path string or a regex.\n"
        "- Regex URLs MUST be written as /pattern/ (single leading/trailing slash). Never use //pattern//.\n\n"
        "ALLOWED STEPS (ONLY these):\n"
        "- await page.goto('<url>')\n"
        "- await page.fill('<selector>', '<value>')\n"
        "- await page.click('<selector>')\n"
        "- await page.waitForSelector('<selector>')\n"
        "- await page.waitForURL('<url>')\n"
        "- await page.waitForURL(/<regex>/)\n\n"
        "ALLOWED ASSERTIONS (ONLY these):\n"
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
        "PLAN REQUIREMENTS:\n"
        "- steps MUST contain at least one 'await page.goto(...)'.\n"
        "- assertions MUST validate the final state of the page (final URL and/or visible content).\n"
        "- Prefer deterministic waits: waitForSelector / waitForURL.\n"
        "- Keep steps minimal (avoid redundant waits/clicks).\n\n"
        "NL_TEST_CASE:\n"
        f"{nl_text}\n"
    )


def get_llm_request_payload(
    nl_text: str, model: str, num_predict: int, num_ctx: int
) -> dict[str, Any]:
    return {
        "model": model,
        "prompt": get_promt(nl_text),
        "stream": False,
        "format": "json",
        "options": {
            "num_ctx": num_ctx,
            "num_predict": num_predict,
            "temperature": 0.1,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            # "seed": 42,
            "stop": ["\n\n\n", "```"],
        },
    }

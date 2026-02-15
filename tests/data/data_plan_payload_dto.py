PLAN_MIN_OK = {
    "steps": ["await page.goto('https://example.com')"],
    "assertions": [],
}

PLAN_OK_WITH_SPACES = {
    "steps": ["   await page.goto('https://example.com')   ", " await page.click('#x') "],
    "assertions": ["  await expect(page.locator('#x')).toBeVisible()  "],
}

PLAN_EXTRA_KEYS = {
    "steps": ["await page.goto('https://example.com')"],
    "assertions": [],
    "foo": 1,
}

PLAN_BAD_STEPS_TYPE = {"steps": "no", "assertions": []}
PLAN_BAD_ASSERT_TYPE = {"steps": ["await page.goto('https://example.com')"], "assertions": "no"}
PLAN_BAD_STEP_ELEM_TYPE = {"steps": [1], "assertions": []}
PLAN_BAD_ASSERT_ELEM_TYPE = {"steps": ["await page.goto('https://example.com')"], "assertions": [1]}

PLAN_NO_GOTO = {
    "steps": ["await page.click('#x')"],
    "assertions": [],
}

PLAN_HAS_DOUBLE_SLASH_REGEX_IN_STEP = {
    "steps": ["await page.goto('https://example.com')", "await page.waitForURL(//dashboard//)"],
    "assertions": [],
}

PLAN_HAS_DOUBLE_SLASH_REGEX_IN_ASSERT = {
    "steps": ["await page.goto('https://example.com')"],
    "assertions": ["await expect(page).toHaveURL(//dashboard//)"],
}

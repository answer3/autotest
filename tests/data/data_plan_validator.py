PLAN_OK = {
    "steps": [
        "await page.goto('https://example.com')",
        "await page.click('#login')",
        "await page.fill('#email', 'a@b.com')",
        "await page.waitForSelector('#dashboard')",
    ],
    "assertions": [
        "await expect(page).toHaveURL('https://example.com/dashboard')",
        "await expect(page.locator('#dashboard')).toBeVisible()",
        "await expect(page.locator('#hello')).toContainText('Hello')",
    ],
}

PLAN_MIN_OK = {
    "steps": ["await page.goto('https://example.com')"],
    "assertions": [],
}

PLAN_WITH_SPACES = {
    "steps": [
        "   await page.goto('https://example.com')   ",
        "await page.click('#btn')   ",
    ],
    "assertions": [
        "  await expect(page.locator('#x')).toBeVisible() ",
    ],
}

PLAN_NO_GOTO = {
    "steps": ["await page.click('#x')"],
    "assertions": [],
}

PLAN_EXTRA_KEYS = {
    "steps": ["await page.goto('https://example.com')"],
    "assertions": [],
    "hacker": "nope",
}

PLAN_BAD_STEP = {
    "steps": [
        "await page.goto('https://example.com')",
        "await page.type('#x', 'y')",
    ],
    "assertions": [],
}

PLAN_BAD_ASSERTION = {
    "steps": ["await page.goto('https://example.com')"],
    "assertions": [
        "await expect(page.locator('#x')).toHaveText('Yo')",
    ],
}

PLAN_BAD_TYPES_1 = {"steps": "no", "assertions": []}
PLAN_BAD_TYPES_2 = {"steps": [1, 2], "assertions": []}
PLAN_BAD_TYPES_3 = {"steps": ["await page.goto('https://example.com')"], "assertions": "no"}
PLAN_BAD_TYPES_4 = {"steps": ["await page.goto('https://example.com')"], "assertions": [1]}

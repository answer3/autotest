BASE_URL_OK = [
    ("https://example.com", "https://example.com"),
    ("https://example.com/", "https://example.com"),
    ("  https://example.com  ", "https://example.com"),
    ("http://example.com", "http://example.com"),
    ("https://example.com:8443", "https://example.com:8443"),
]

BASE_URL_BAD = [
    ("", "site_domain is empty"),
    ("   ", "site_domain is empty"),
    ("example.com", "must include http/https scheme"),
    ("ftp://example.com", "must include http/https scheme"),
    ("https://", "netloc is empty"),
    ("https://example.com/path", "must not include path/query/fragment"),
    ("https://example.com/path/", "must not include path/query/fragment"),
    ("https://example.com/?a=1", "must not include path/query/fragment"),
    ("https://example.com#x", "must not include path/query/fragment"),
]

JS_REGEX_NORMALIZE = [
    ("await page.waitForURL(//foo//)", "await page.waitForURL(/foo/)"),
    ("await expect(page).toHaveURL(//bar//)", "await expect(page).toHaveURL(/bar/)"),
    ("await page.waitForURL( /a.+b/ )", "await page.waitForURL( /a.+b/ )"),  # уже норм
    ("noop", "noop"),
    ("waitForURL(//a//) toHaveURL(//b//)", "waitForURL(/a/) toHaveURL(/b/)"),
]

PLACEHOLDERS_OK = {"<EMAIL>": "a@b.com", "<PWD>": "secret"}

TEXT_WITH_PLACEHOLDERS = "await page.fill('#email', '<EMAIL>')"
TEXT_WITH_UNRESOLVED = "await page.fill('#email', '<MISSING>')"

PLAN_OK = {
    "steps": [
        "await page.goto('https://example.com')",
        "await page.fill('#email', '<EMAIL>')",
        "await page.waitForURL(//dashboard//)",
    ],
    "assertions": [
        "await expect(page).toHaveURL(//dashboard//)",
        "await expect(page.locator('#x')).toContainText('<PWD>')",
    ],
}

PLAN_RENDERED_OK = {
    "steps": [
        "await page.goto('https://example.com')",
        "await page.fill('#email', 'a@b.com')",
        "await page.waitForURL(/dashboard/)",
    ],
    "assertions": [
        "await expect(page).toHaveURL(/dashboard/)",
        "await expect(page.locator('#x')).toContainText('secret')",
    ],
}

PLAN_BAD_STEPS_TYPE = {"steps": "nope", "assertions": []}
PLAN_BAD_ASSERT_TYPE = {"steps": ["await page.goto('https://example.com')"], "assertions": "nope"}
PLAN_BAD_STEP_ELEM_TYPE = {"steps": [1], "assertions": []}
PLAN_BAD_ASSERT_ELEM_TYPE = {"steps": ["await page.goto('https://example.com')"], "assertions": [1]}

PLAN_WITH_UNRESOLVED = {
    "steps": ["await page.goto('https://example.com')", "await page.fill('#x', '<MISSING>')"],
    "assertions": [],
}

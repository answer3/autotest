import re

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

# Placeholders like <login>, <password>
PLACEHOLDER_RE = re.compile(r"<[a-zA-Z0-9_-]+>")

# Reject broken JS-like regex delimiter `//path//`
BAD_DOUBLE_SLASH_URL = re.compile(r"\(\s*//")

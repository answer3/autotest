from app.models.enums import TestRunStatus

TEST_RUN_PARAMS = {
    "playwright_headless": True,
    "playwright_timeout_ms": 30000,
    "playwright_browser": "chromium",
}

TEST_RUN_DOMAIN = "http://example.com"

TEST_RUN_REQUEST_1 = {
    "run_params": TEST_RUN_PARAMS,
    "placeholders": {"foo": "bar"},
    "site_domain": TEST_RUN_DOMAIN,
}

TEST_RUN_DATA_CREATE_1 = {
    "run_params": TEST_RUN_PARAMS,
    "site_domain": TEST_RUN_DOMAIN,
}

TEST_RUN_DATA_CREATE_PASSED_1 = {
    "run_params": TEST_RUN_PARAMS,
    "site_domain": TEST_RUN_DOMAIN,
    "status": TestRunStatus.passed,
}

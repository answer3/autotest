import app.workers.test_runner.patterns as runner_patterns
from app.exceptions import PlanExecutionError


def _validate_line_no_double_slash_regex(line: str) -> None:
    # catch waitForURL(//secure//) and toHaveURL(//secure//)
    if runner_patterns.BAD_DOUBLE_SLASH_URL.search(line):
        raise PlanExecutionError(f"Invalid regex delimiter //...// in: {line}")

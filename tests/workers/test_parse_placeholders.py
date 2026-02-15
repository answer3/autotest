import pytest

from app.workers.test_runner.renderer import parse_placeholders


@pytest.mark.parametrize(
    "raw, expected",
    [
        (None, {}),
        ("{}", {}),
        ('{"a":"b"}', {"a": "b"}),
        ({"a": "b"}, {"a": "b"}),
        ("null", {}),                # json -> None
        ("[]", {}),                  # json -> list
        ("not-json", {}),            # decode error
        ({"a": 1}, {}),              # non-str value
        ({1: "b"}, {}),              # non-str key
        ([], {}),                    # non-dict
        (123, {}),                   # non-dict
        ({"a": "b", "c": "d"}, {"a": "b", "c": "d"}),
    ],
)
def test_parse_placeholders(raw, expected):
    assert parse_placeholders(raw) == expected

import json

from src.scrapers.base import FetchResult
from src.scrapers.twitter_playwright import _load_valid_cookie_sets


def test_invalid_cookie_file_does_not_block_later_valid_file(tmp_path):
    invalid = tmp_path / "x_cookies_bad.json"
    valid = tmp_path / "x_cookies_good.json"
    invalid.write_text("{", encoding="utf-8")
    valid.write_text(
        json.dumps([{"name": "auth_token", "value": "placeholder", "domain": ".x.com"}]),
        encoding="utf-8",
    )
    result = FetchResult()

    cookie_sets = _load_valid_cookie_sets([invalid, valid], result)

    assert cookie_sets == [
        (1, [{"name": "auth_token", "value": "placeholder", "domain": ".x.com", "path": "/", "secure": True, "httpOnly": False}])
    ]
    assert set(result.failures) == {"cookie_file_1"}
    assert "placeholder" not in str(result.failures)

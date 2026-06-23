"""Tests para rate limiting de API."""

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from src.api.rate_limit import check_rate_limit


def _make_request(ip: str = "10.0.0.1") -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/ingest",
        "headers": [],
        "client": (ip, 12345),
    }
    return Request(scope)


def test_rate_limit_allows_under_limit():
    request = _make_request("10.0.0.2")
    check_rate_limit(request, "test-scope", 5)
    check_rate_limit(request, "test-scope", 5)


def test_rate_limit_blocks_over_limit():
    request = _make_request("10.0.0.3")
    for _ in range(3):
        check_rate_limit(request, "test-block", 3)
    with pytest.raises(HTTPException) as exc:
        check_rate_limit(request, "test-block", 3)
    assert exc.value.status_code == 429

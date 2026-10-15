import pytest
from fastapi import HTTPException
from app.security.url_safety import validate_url_safety


def test_ssrf_disallow_localhost():
    with pytest.raises(HTTPException) as exc_info:
        validate_url_safety("http://localhost:8080/admin")
    assert exc_info.value.status_code == 403


def test_ssrf_disallow_loopback_ip():
    with pytest.raises(HTTPException) as exc_info:
        validate_url_safety("http://127.0.0.1:8000/secret")
    assert exc_info.value.status_code == 403


def test_ssrf_disallow_scheme():
    with pytest.raises(HTTPException) as exc_info:
        validate_url_safety("file:///etc/passwd")
    assert exc_info.value.status_code == 400


def test_allow_valid_public_domain():
    url = validate_url_safety("https://en.wikipedia.org/wiki/Earth")
    assert url == "https://en.wikipedia.org/wiki/Earth"

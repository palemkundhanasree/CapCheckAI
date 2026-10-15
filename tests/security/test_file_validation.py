import pytest
from fastapi import HTTPException
from app.security.file_validation import (
    sanitize_filename,
    validate_file_size,
    inspect_magic_bytes
)


def test_sanitize_filename_path_traversal():
    bad_name = "../../../etc/passwd"
    clean = sanitize_filename(bad_name)
    assert "/" not in clean
    assert ".." not in clean
    assert clean == "passwd"


def test_validate_file_size_limit():
    ten_mb = b"0" * (10 * 1024 * 1024)
    # 5MB limit should fail
    with pytest.raises(HTTPException) as exc_info:
        validate_file_size(ten_mb, max_mb=5, file_category="Image")
    assert exc_info.value.status_code == 413


def test_inspect_magic_bytes():
    png_header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    assert inspect_magic_bytes(png_header) == "image/png"

    jpeg_header = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    assert inspect_magic_bytes(jpeg_header) == "image/jpeg"

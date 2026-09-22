import pytest

from function_app import (sanitize_filename, sanitize_job_description, validate_request)

VALID_JD = "A" * 120


def test_rejects_file_larger_than_5_mb():
    file_bytes = b"%PDF-" + (b"A" * (5 * 1024 * 1024))

    with pytest.raises(ValueError, match="Maximum size is 5 MB"):
        validate_request("resume.pdf", file_bytes, VALID_JD)


def test_accepts_file_at_5_mb_limit():
    prefix = b"%PDF-"
    file_bytes = prefix + (b"A" * ((5 * 1024 * 1024) - len(prefix)))

    validate_request("resume.pdf", file_bytes, VALID_JD)


def test_rejects_unsupported_extension():
    with pytest.raises(ValueError, match="Unsupported resume file type"):
        validate_request("resume.exe", b"dummy content", VALID_JD)


def test_rejects_fake_pdf_content():
    with pytest.raises(ValueError, match="does not match PDF format"):
        validate_request("resume.pdf", b"not-a-real-pdf", VALID_JD)


def test_rejects_fake_docx_content():
    with pytest.raises(ValueError, match="does not match DOCX format"):
        validate_request("resume.docx", b"not-a-real-docx", VALID_JD)


def test_rejects_invalid_utf8_txt():
    with pytest.raises(ValueError, match="valid UTF-8"):
        validate_request("resume.txt", b"\xff\xfe\x00\x00", VALID_JD)


def test_accepts_valid_txt():
    validate_request(
        "resume.txt",
        b"Python Azure DevOps Engineer with CI/CD experience.",
        VALID_JD,
    )


def test_sanitize_filename_removes_windows_path():
    result = sanitize_filename(r"C:\Users\Test\Documents\resume.pdf")
    assert result == "resume.pdf"


def test_sanitize_filename_removes_unix_path():
    result = sanitize_filename("/tmp/uploads/resume.pdf")
    assert result == "resume.pdf"


def test_sanitize_filename_removes_null_bytes():
    result = sanitize_filename("resume\x00.pdf")
    assert result == "resume.pdf"


def test_sanitize_filename_trims_whitespace():
    result = sanitize_filename("   resume.pdf   ")
    assert result == "resume.pdf"


def test_sanitize_filename_rejects_non_string():
    with pytest.raises(ValueError, match="must be a string"):
        sanitize_filename(123)


def test_sanitize_job_description_trims_whitespace():
    jd = "   " + ("A" * 120) + "   "
    result = sanitize_job_description(jd)

    assert result == "A" * 120


def test_sanitize_job_description_rejects_blank_text():
    with pytest.raises(ValueError, match="Job description is required"):
        sanitize_job_description("     ")


def test_sanitize_job_description_rejects_too_short_text():
    with pytest.raises(ValueError, match="too short"):
        sanitize_job_description("A" * 99)


def test_sanitize_job_description_accepts_minimum_length():
    result = sanitize_job_description("A" * 100)
    assert len(result) == 100


def test_sanitize_job_description_rejects_more_than_50000_characters():
    with pytest.raises(ValueError, match="Maximum length is 50,000"):
        sanitize_job_description("A" * 50_001)


def test_sanitize_job_description_accepts_50000_characters():
    result = sanitize_job_description("A" * 50_000)
    assert len(result) == 50_000


def test_sanitize_job_description_rejects_non_string():
    with pytest.raises(ValueError, match="must be a string"):
        sanitize_job_description(["not", "a", "string"])
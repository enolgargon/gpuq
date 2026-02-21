import re
import pytest

from gpuq_cli.utils import (
    now_iso8601,
    validate_iso8601,
    generate_job_id,
    get_current_user,
)


# -------------------------
# now_iso8601
# -------------------------

def test_now_iso8601_returns_valid_format():
    ts = now_iso8601()

    # Should not raise
    validate_iso8601(ts, "timestamp")

    # Basic format check: 2026-02-21T10:15:00Z
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", ts)


# -------------------------
# validate_iso8601
# -------------------------

def test_validate_iso8601_accepts_valid_timestamp():
    valid = "2026-02-21T10:15:00Z"
    validate_iso8601(valid, "created_at")


def test_validate_iso8601_accepts_none():
    validate_iso8601(None, "optional_field")


def test_validate_iso8601_rejects_invalid_format():
    invalid = "2026-02-21"

    with pytest.raises(ValueError):
        validate_iso8601(invalid, "created_at")


def test_validate_iso8601_rejects_garbage():
    invalid = "not-a-date"

    with pytest.raises(ValueError):
        validate_iso8601(invalid, "created_at")


# -------------------------
# generate_job_id
# -------------------------

def test_generate_job_id_prefix():
    job_id = generate_job_id()

    assert job_id.startswith("job-")


def test_generate_job_id_uniqueness():
    job_id_1 = generate_job_id()
    job_id_2 = generate_job_id()

    assert job_id_1 != job_id_2


def test_generate_job_id_format():
    job_id = generate_job_id()

    # Expected format: job-xxxxxxxx (8 hex chars)
    assert re.match(r"job-[0-9a-f]{8}", job_id)


# -------------------------
# get_current_user
# -------------------------

def test_get_current_user_returns_non_empty_string():
    user = get_current_user()

    assert isinstance(user, str)
    assert user != ""
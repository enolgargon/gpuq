import pytest

from gpuq_cli.jobs import Job
from gpuq_cli.errors import JobValidationError
from gpuq_cli.utils import now_iso8601


# -------------------------
# Helpers
# -------------------------

def valid_job_kwargs():
    return {
        "job_id": "job-12345678",
        "user": "alice",
        "project_path": "/home/alice/project",
        "compose_file": "docker-compose.yml",
        "created_at": "2026-02-21T10:15:00Z",
        "description": "Test job",
        "started_at": None,
        "finished_at": None,
    }


# -------------------------
# Job creation
# -------------------------

def test_create_valid_job():
    job = Job(**valid_job_kwargs())

    assert job.job_id == "job-12345678"
    assert job.user == "alice"
    assert job.started_at is None
    assert job.finished_at is None


# -------------------------
# Validation errors
# -------------------------

@pytest.mark.parametrize(
    "field,value",
    [
        ("job_id", ""),
        ("user", ""),
        ("project_path", ""),
        ("compose_file", ""),
        ("created_at", ""),
    ],
)
def test_required_fields_must_not_be_empty(field, value):
    kwargs = valid_job_kwargs()
    kwargs[field] = value

    with pytest.raises(JobValidationError):
        Job(**kwargs)


def test_invalid_created_at_format():
    kwargs = valid_job_kwargs()
    kwargs["created_at"] = "2026-02-21"

    with pytest.raises(JobValidationError):
        Job(**kwargs)


def test_invalid_started_at_format():
    kwargs = valid_job_kwargs()
    kwargs["started_at"] = "invalid-date"

    with pytest.raises(JobValidationError):
        Job(**kwargs)


def test_invalid_finished_at_format():
    kwargs = valid_job_kwargs()
    kwargs["finished_at"] = "invalid-date"

    with pytest.raises(JobValidationError):
        Job(**kwargs)


# -------------------------
# Serialization / Deserialization
# -------------------------

def test_to_yaml_and_from_yaml_roundtrip():
    job = Job(**valid_job_kwargs())

    yaml_data = job.to_yaml()
    loaded_job = Job.from_yaml(yaml_data)

    assert loaded_job.job_id == job.job_id
    assert loaded_job.user == job.user
    assert loaded_job.project_path == job.project_path
    assert loaded_job.compose_file == job.compose_file
    assert loaded_job.created_at == job.created_at
    assert loaded_job.description == job.description
    assert loaded_job.started_at == job.started_at
    assert loaded_job.finished_at == job.finished_at


def test_from_yaml_missing_required_field():
    yaml_data = """
job_id: job-123
user: alice
"""

    with pytest.raises(JobValidationError):
        Job.from_yaml(yaml_data)


def test_from_yaml_invalid_yaml():
    yaml_data = "::: this is not yaml :::"

    with pytest.raises(JobValidationError):
        Job.from_yaml(yaml_data)


def test_from_yaml_non_mapping():
    yaml_data = "- just\n- a\n- list"

    with pytest.raises(JobValidationError):
        Job.from_yaml(yaml_data)


# -------------------------
# Job state helpers
# -------------------------

def test_mark_started_sets_started_at():
    job = Job(**valid_job_kwargs())
    ts = now_iso8601()

    job.mark_started(ts)

    assert job.started_at == ts


def test_mark_finished_sets_finished_at():
    job = Job(**valid_job_kwargs())
    ts = now_iso8601()

    job.mark_finished(ts)

    assert job.finished_at == ts


def test_mark_started_rejects_invalid_timestamp():
    job = Job(**valid_job_kwargs())

    with pytest.raises(JobValidationError):
        job.mark_started("invalid-date")


def test_mark_finished_rejects_invalid_timestamp():
    job = Job(**valid_job_kwargs())

    with pytest.raises(JobValidationError):
        job.mark_finished("invalid-date")
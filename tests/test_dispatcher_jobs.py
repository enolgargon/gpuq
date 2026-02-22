import pytest
import yaml

from gpuq_dispatcher.jobs import Job
from gpuq_dispatcher.errors import QueueError


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def valid_job_dict():
    return {
        "user": "alice",
        "project_path": "/home/alice/project",
        "compose_file": "docker-compose.yml",
        "created_at": "2026-02-22T10:00:00Z",
        "description": "test job",
        "started_at": None,
        "finished_at": None,
    }


# ------------------------------------------------------------------
# from_dict
# ------------------------------------------------------------------


def test_job_from_dict_valid():
    job = Job.from_dict("job-123", valid_job_dict())

    assert job.job_id == "job-123"
    assert job.user == "alice"
    assert job.project_path == "/home/alice/project"
    assert job.compose_file == "docker-compose.yml"
    assert job.created_at == "2026-02-22T10:00:00Z"
    assert job.description == "test job"
    assert job.started_at is None
    assert job.finished_at is None


def test_job_from_dict_missing_required_field():
    data = valid_job_dict()
    del data["user"]

    with pytest.raises(QueueError):
        Job.from_dict("job-123", data)


def test_job_from_dict_uses_default_compose_file():
    data = valid_job_dict()
    del data["compose_file"]

    job = Job.from_dict("job-123", data)

    assert job.compose_file == "docker-compose.yml"


def test_job_from_dict_ignores_extra_fields():
    data = valid_job_dict()
    data["extra_field"] = "ignored"

    job = Job.from_dict("job-123", data)

    assert not hasattr(job, "extra_field")


# ------------------------------------------------------------------
# from_yaml
# ------------------------------------------------------------------


def test_job_from_yaml_valid():
    data = valid_job_dict()
    yaml_content = yaml.safe_dump(data)

    job = Job.from_yaml("job-456", yaml_content)

    assert job.job_id == "job-456"
    assert job.user == "alice"


def test_job_from_yaml_invalid_yaml():
    yaml_content = "user: [unclosed-list"

    with pytest.raises(QueueError):
        Job.from_yaml("job-456", yaml_content)


def test_job_from_yaml_non_mapping():
    yaml_content = yaml.safe_dump(["not", "a", "dict"])

    with pytest.raises(QueueError):
        Job.from_yaml("job-456", yaml_content)


# ------------------------------------------------------------------
# Serialization
# ------------------------------------------------------------------


def test_job_to_dict_roundtrip():
    job = Job.from_dict("job-789", valid_job_dict())

    data = job.to_dict()

    assert data["user"] == "alice"
    assert data["project_path"] == "/home/alice/project"
    assert data["created_at"] == "2026-02-22T10:00:00Z"


def test_job_to_yaml_roundtrip():
    job = Job.from_dict("job-789", valid_job_dict())

    yaml_content = job.to_yaml()
    data = yaml.safe_load(yaml_content)

    assert data["user"] == "alice"
    assert data["project_path"] == "/home/alice/project"


# ------------------------------------------------------------------
# State helpers
# ------------------------------------------------------------------


def test_mark_started_sets_timestamp():
    job = Job.from_dict("job-001", valid_job_dict())

    job.mark_started("2026-02-22T10:05:00Z")

    assert job.started_at == "2026-02-22T10:05:00Z"


def test_mark_finished_sets_timestamp():
    job = Job.from_dict("job-002", valid_job_dict())

    job.mark_finished("2026-02-22T10:30:00Z")

    assert job.finished_at == "2026-02-22T10:30:00Z"
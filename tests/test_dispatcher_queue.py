import pytest
import yaml

from gpuq_dispatcher import queue
from gpuq_dispatcher.jobs import Job
from gpuq_dispatcher.errors import QueueError


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def valid_job_yaml():
    return yaml.safe_dump(
        {
            "user": "alice",
            "project_path": "/home/alice/project",
            "compose_file": "docker-compose.yml",
            "created_at": "2026-02-22T10:00:00Z",
            "description": "test job",
            "started_at": None,
            "finished_at": None,
        }
    )


def write_job(tmp_path, state, job_id):
    state_dir = tmp_path / state
    state_dir.mkdir(parents=True, exist_ok=True)

    job_file = state_dir / f"{job_id}.yaml"
    job_file.write_text(valid_job_yaml())

    return job_file


@pytest.fixture
def queue_root(tmp_path, monkeypatch):
    """
    Patch QUEUE_ROOT to point to a temporary directory.
    """
    monkeypatch.setattr(queue, "QUEUE_ROOT", str(tmp_path))
    return tmp_path


# ------------------------------------------------------------------
# Basic operations
# ------------------------------------------------------------------


def test_list_jobs_empty(queue_root):
    jobs = queue.list_jobs()
    assert jobs == []


def test_list_jobs_single_job(queue_root):
    write_job(queue_root, "queued", "job-1")

    jobs = queue.list_jobs()

    assert len(jobs) == 1
    assert jobs[0].job_id == "job-1"


def test_get_job(queue_root):
    write_job(queue_root, "queued", "job-42")

    job = queue.get_job("job-42")

    assert job.job_id == "job-42"
    assert job.user == "alice"


def test_get_job_not_found(queue_root):
    with pytest.raises(QueueError):
        queue.get_job("missing-job")


# ------------------------------------------------------------------
# State transitions
# ------------------------------------------------------------------


def test_mark_job_running(queue_root):
    write_job(queue_root, "queued", "job-1")

    job = queue.mark_job_running(
        "job-1",
        started_at="2026-02-22T10:05:00Z",
    )

    assert job.started_at == "2026-02-22T10:05:00Z"

    # job moved to running
    assert (queue_root / "queued" / "job-1.yaml").exists() is False
    assert (queue_root / "running" / "job-1.yaml").exists()


def test_mark_job_finished_success(queue_root):
    write_job(queue_root, "running", "job-2")

    job = queue.mark_job_finished(
        "job-2",
        finished_at="2026-02-22T10:30:00Z",
        success=True,
    )

    assert job.finished_at == "2026-02-22T10:30:00Z"
    assert (queue_root / "finished" / "job-2.yaml").exists()


def test_mark_job_finished_failed(queue_root):
    write_job(queue_root, "running", "job-3")

    job = queue.mark_job_finished(
        "job-3",
        finished_at="2026-02-22T10:30:00Z",
        success=False,
    )

    assert (queue_root / "failed" / "job-3.yaml").exists()


# ------------------------------------------------------------------
# Cancellation
# ------------------------------------------------------------------


def test_cancel_queued_job(queue_root):
    write_job(queue_root, "queued", "job-4")

    job = queue.mark_job_canceled("job-4")

    assert job.job_id == "job-4"
    assert (queue_root / "canceled" / "job-4.yaml").exists()


def test_cancel_running_job(queue_root):
    write_job(queue_root, "running", "job-5")

    job = queue.mark_job_canceled("job-5")

    assert job.job_id == "job-5"
    assert (queue_root / "canceled" / "job-5.yaml").exists()


def test_cancel_invalid_state(queue_root):
    write_job(queue_root, "finished", "job-6")

    with pytest.raises(QueueError):
        queue.mark_job_canceled("job-6")


# ------------------------------------------------------------------
# Filtering
# ------------------------------------------------------------------


def test_get_queued_jobs(queue_root):
    write_job(queue_root, "queued", "job-a")
    write_job(queue_root, "running", "job-b")
    write_job(queue_root, "queued", "job-c")

    jobs = queue.get_queued_jobs()
    job_ids = {job.job_id for job in jobs}

    assert job_ids == {"job-a", "job-c"}
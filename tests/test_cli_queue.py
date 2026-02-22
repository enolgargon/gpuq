import pytest
import yaml

from gpuq_cli import queue
from gpuq_cli.jobs import Job
from gpuq_cli.errors import QueueError


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def valid_job(job_id="job-1"):
    return Job(
        job_id=job_id,
        user="alice",
        project_path="/home/alice/project",
        compose_file="docker-compose.yml",
        created_at="2026-02-22T10:00:00Z",
        description="test job",
    )


@pytest.fixture
def queue_root(tmp_path, monkeypatch):
    """
    Patch QUEUE_ROOT to point to a temporary directory.
    """
    monkeypatch.setattr(queue, "QUEUE_ROOT", tmp_path)
    return tmp_path


# ------------------------------------------------------------------
# enqueue_job
# ------------------------------------------------------------------


def test_enqueue_job_creates_job_file(queue_root):
    job = valid_job("job-1")

    queue.enqueue_job(job)

    job_file = queue_root / "queued" / "job-1.yaml"
    assert job_file.exists()


def test_enqueue_job_duplicate_raises(queue_root):
    job = valid_job("job-1")

    queue.enqueue_job(job)

    with pytest.raises(QueueError):
        queue.enqueue_job(job)


# ------------------------------------------------------------------
# list_jobs
# ------------------------------------------------------------------


def test_list_jobs_empty(queue_root):
    jobs = queue.list_jobs()
    assert jobs == []


def test_list_jobs_all_states(queue_root):
    queue.enqueue_job(valid_job("job-a"))
    queue.enqueue_job(valid_job("job-b"))

    jobs = queue.list_jobs()
    job_ids = {job.job_id for job in jobs}

    assert job_ids == {"job-a", "job-b"}


def test_list_jobs_specific_state(queue_root):
    queue.enqueue_job(valid_job("job-a"))
    queue.enqueue_job(valid_job("job-b"))

    queue.move_job("job-a", "running")

    jobs = queue.list_jobs(state="queued")
    job_ids = {job.job_id for job in jobs}

    assert job_ids == {"job-b"}


def test_list_jobs_invalid_state(queue_root):
    with pytest.raises(QueueError):
        queue.list_jobs(state="invalid")


# ------------------------------------------------------------------
# load_job
# ------------------------------------------------------------------


def test_load_job(queue_root):
    queue.enqueue_job(valid_job("job-x"))

    job = queue.load_job("job-x")

    assert job.job_id == "job-x"
    assert job.user == "alice"


def test_load_job_not_found(queue_root):
    with pytest.raises(QueueError):
        queue.load_job("missing")


# ------------------------------------------------------------------
# move_job
# ------------------------------------------------------------------


def test_move_job(queue_root):
    queue.enqueue_job(valid_job("job-1"))

    queue.move_job("job-1", "running")

    assert not (queue_root / "queued" / "job-1.yaml").exists()
    assert (queue_root / "running" / "job-1.yaml").exists()


def test_move_job_invalid_state(queue_root):
    queue.enqueue_job(valid_job("job-1"))

    with pytest.raises(QueueError):
        queue.move_job("job-1", "invalid")


def test_move_job_not_found(queue_root):
    with pytest.raises(QueueError):
        queue.move_job("missing", "queued")


# ------------------------------------------------------------------
# cancel_job
# ------------------------------------------------------------------


def test_cancel_queued_job(queue_root):
    queue.enqueue_job(valid_job("job-1"))

    queue.cancel_job("job-1")

    assert (queue_root / "canceled" / "job-1.yaml").exists()


def test_cancel_running_job(queue_root):
    queue.enqueue_job(valid_job("job-1"))
    queue.move_job("job-1", "running")

    queue.cancel_job("job-1")

    assert (queue_root / "canceled" / "job-1.yaml").exists()


def test_cancel_finished_job_fails(queue_root):
    queue.enqueue_job(valid_job("job-1"))
    queue.move_job("job-1", "finished")

    with pytest.raises(QueueError):
        queue.cancel_job("job-1")


# ------------------------------------------------------------------
# mark_job_started
# ------------------------------------------------------------------


def test_mark_job_started(queue_root):
    queue.enqueue_job(valid_job("job-1"))

    queue.mark_job_started("job-1")

    job = queue.load_job("job-1")

    assert job.started_at is not None
    assert (queue_root / "running" / "job-1.yaml").exists()


# ------------------------------------------------------------------
# mark_job_finished
# ------------------------------------------------------------------


def test_mark_job_finished_success(queue_root):
    queue.enqueue_job(valid_job("job-1"))
    queue.mark_job_started("job-1")

    queue.mark_job_finished("job-1", success=True)

    job = queue.load_job("job-1")

    assert job.finished_at is not None
    assert (queue_root / "finished" / "job-1.yaml").exists()


def test_mark_job_finished_failed(queue_root):
    queue.enqueue_job(valid_job("job-1"))
    queue.mark_job_started("job-1")

    queue.mark_job_finished("job-1", success=False)

    assert (queue_root / "failed" / "job-1.yaml").exists()
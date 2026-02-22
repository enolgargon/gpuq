import pytest

from gpuq_dispatcher.scheduler import Scheduler
from gpuq_dispatcher.jobs import Job


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def make_job(job_id: str, created_at: str) -> Job:
    return Job(
        job_id=job_id,
        user="alice",
        project_path="/home/alice/project",
        compose_file="docker-compose.yml",
        created_at=created_at,
        description="test job",
    )


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------


def test_select_next_job_empty_list():
    scheduler = Scheduler()

    job = scheduler.select_next_job([])

    assert job is None


def test_select_next_job_single_job():
    scheduler = Scheduler()
    job1 = make_job("job-1", "2026-02-22T10:00:00Z")

    selected = scheduler.select_next_job([job1])

    assert selected is job1


def test_select_next_job_fifo_order():
    scheduler = Scheduler()

    job1 = make_job("job-1", "2026-02-22T10:00:00Z")
    job2 = make_job("job-2", "2026-02-22T10:05:00Z")
    job3 = make_job("job-3", "2026-02-22T10:10:00Z")

    selected = scheduler.select_next_job([job3, job2, job1])

    # FIFO: oldest created_at wins
    assert selected.job_id == "job-1"


def test_select_next_job_same_timestamp_stable():
    scheduler = Scheduler()

    job1 = make_job("job-1", "2026-02-22T10:00:00Z")
    job2 = make_job("job-2", "2026-02-22T10:00:00Z")

    selected = scheduler.select_next_job([job2, job1])

    assert selected.created_at == "2026-02-22T10:00:00Z"
    assert selected.job_id in {"job-1", "job-2"}
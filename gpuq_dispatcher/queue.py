import os
import shutil
from typing import List, Optional

from .config import QUEUE_ROOT, QUEUE_STATES
from .errors import QueueError
from .jobs import Job


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


def _ensure_queue_structure() -> None:
    for state in QUEUE_STATES:
        os.makedirs(os.path.join(QUEUE_ROOT, state), exist_ok=True)


def _job_file_path(state: str, job_id: str) -> str:
    return os.path.join(QUEUE_ROOT, state, f"{job_id}.yaml")


def _find_job_state(job_id: str) -> Optional[str]:
    for state in QUEUE_STATES:
        path = _job_file_path(state, job_id)
        if os.path.exists(path):
            return state
    return None


def _load_job_from_state(state: str, job_id: str) -> Job:
    path = _job_file_path(state, job_id)

    if not os.path.exists(path):
        raise QueueError(f"Job {job_id} not found in state '{state}'")

    try:
        with open(path, "r") as f:
            yaml_content = f.read()
    except Exception as e:
        raise QueueError(f"Failed to read job {job_id}: {e}") from e

    return Job.from_yaml(job_id, yaml_content)


def _write_job(state: str, job: Job) -> None:
    path = _job_file_path(state, job.job_id)

    try:
        with open(path, "w") as f:
            f.write(job.to_yaml())
    except Exception as e:
        raise QueueError(f"Failed to write job {job.job_id}: {e}") from e


def _move_job(job_id: str, from_state: str, to_state: str) -> None:
    src = _job_file_path(from_state, job_id)
    dst = _job_file_path(to_state, job_id)

    if not os.path.exists(src):
        raise QueueError(
            f"Job {job_id} not found in state '{from_state}'"
        )

    try:
        shutil.move(src, dst)
    except Exception as e:
        raise QueueError(
            f"Failed to move job {job_id} "
            f"from '{from_state}' to '{to_state}': {e}"
        ) from e


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------


def list_jobs(state: Optional[str] = None) -> List[Job]:
    _ensure_queue_structure()

    jobs: List[Job] = []
    states = [state] if state else QUEUE_STATES

    for st in states:
        if st not in QUEUE_STATES:
            continue

        dir_path = os.path.join(QUEUE_ROOT, st)

        try:
            filenames = os.listdir(dir_path)
        except FileNotFoundError:
            continue

        for filename in filenames:
            if not filename.endswith(".yaml"):
                continue

            job_id = filename[:-5]  # remove ".yaml"
            job = _load_job_from_state(st, job_id)
            jobs.append(job)

    return jobs


def get_job(job_id: str) -> Job:
    _ensure_queue_structure()

    state = _find_job_state(job_id)

    if not state:
        raise QueueError(f"Job not found: {job_id}")

    return _load_job_from_state(state, job_id)


def get_queued_jobs() -> List[Job]:
    return list_jobs(state="queued")

def get_running_jobs() -> List[Job]:
    return list_jobs(state="running")


def mark_job_running(job_id: str, started_at: str) -> Job:
    _ensure_queue_structure()

    job = _load_job_from_state("queued", job_id)

    job.mark_started(started_at)

    _move_job(job_id, "queued", "running")
    _write_job("running", job)

    return job


def mark_job_finished(
    job_id: str,
    finished_at: str,
    success: bool,
) -> Job:
    _ensure_queue_structure()

    job = _load_job_from_state("running", job_id)

    job.mark_finished(finished_at)

    target_state = "finished" if success else "failed"

    _move_job(job_id, "running", target_state)
    _write_job(target_state, job)

    return job


def mark_job_canceled(job_id: str) -> Job:
    _ensure_queue_structure()

    state = _find_job_state(job_id)

    if state not in ("queued", "running"):
        raise QueueError(
            f"Job {job_id} cannot be canceled from state '{state}'"
        )

    job = _load_job_from_state(state, job_id)

    _move_job(job_id, state, "canceled")
    _write_job("canceled", job)

    return job
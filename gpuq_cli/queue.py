from pathlib import Path
from typing import List, Optional
import os

from .jobs import Job
from .errors import QueueError
from .utils import now_iso8601


# -------------------------
# Configuration
# -------------------------

DEFAULT_QUEUE_ROOT = Path("./queue")
QUEUE_ROOT = Path(os.environ.get("GPUQ_QUEUE_ROOT", DEFAULT_QUEUE_ROOT))

STATES = ["queued", "running", "finished", "failed", "canceled"]


# -------------------------
# Internal helpers
# -------------------------

def _ensure_queue_structure() -> None:
    """
    Ensure that the queue root and state directories exist.
    """
    QUEUE_ROOT.mkdir(parents=True, exist_ok=True)
    for state in STATES:
        (QUEUE_ROOT / state).mkdir(exist_ok=True)


def _validate_state(state: str) -> None:
    if state not in STATES:
        raise QueueError(f"Invalid queue state: {state}")


def _job_path(state: str, job_id: str) -> Path:
    _validate_state(state)
    return QUEUE_ROOT / state / f"{job_id}.yaml"


def _find_job(job_id: str) -> Optional[Path]:
    """
    Search for a job across all states.
    Returns the path if found, otherwise None.
    """
    for state in STATES:
        path = _job_path(state, job_id)
        if path.exists():
            return path
    return None


# -------------------------
# Public API
# -------------------------

def enqueue_job(job: Job) -> None:
    """
    Add a new job to the 'queued' state.
    """
    _ensure_queue_structure()

    job_file = _job_path("queued", job.job_id)

    if _find_job(job.job_id) is not None:
        raise QueueError(f"Job '{job.job_id}' already exists")

    try:
        job_file.write_text(job.to_yaml())
    except OSError as e:
        raise QueueError(f"Failed to write job file: {e}")


def list_jobs(state: Optional[str] = None) -> List[Job]:
    """
    List jobs.
    If state is provided, list only jobs in that state.
    Otherwise list all jobs across states.
    """
    _ensure_queue_structure()

    jobs: List[Job] = []

    states_to_check = [state] if state else STATES

    for s in states_to_check:
        _validate_state(s)
        state_dir = QUEUE_ROOT / s

        for file in state_dir.glob("*.yaml"):
            try:
                content = file.read_text()
                job = Job.from_yaml(content)
                jobs.append(job)
            except Exception as e:
                raise QueueError(f"Failed to load job '{file.name}': {e}")

    return jobs


def load_job(job_id: str) -> Job:
    """
    Load a job regardless of its current state.
    """
    _ensure_queue_structure()

    job_path = _find_job(job_id)

    if job_path is None:
        raise QueueError(f"Job '{job_id}' not found")

    try:
        content = job_path.read_text()
        return Job.from_yaml(content)
    except Exception as e:
        raise QueueError(f"Failed to load job '{job_id}': {e}")


def move_job(job_id: str, target_state: str) -> None:
    """
    Move a job to a different state.
    """
    _ensure_queue_structure()
    _validate_state(target_state)

    current_path = _find_job(job_id)

    if current_path is None:
        raise QueueError(f"Job '{job_id}' not found")

    target_path = _job_path(target_state, job_id)

    if target_path.exists():
        raise QueueError(
            f"Job '{job_id}' already exists in state '{target_state}'"
        )

    try:
        current_path.rename(target_path)
    except OSError as e:
        raise QueueError(f"Failed to move job '{job_id}': {e}")


def cancel_job(job_id: str) -> None:
    """
    Cancel a job.
    If it is queued, it is moved to 'canceled'.
    If it is running, it is also moved to 'canceled'.
    """
    _ensure_queue_structure()

    current_path = _find_job(job_id)

    if current_path is None:
        raise QueueError(f"Job '{job_id}' not found")

    current_state = current_path.parent.name

    if current_state in ["finished", "failed", "canceled"]:
        raise QueueError(
            f"Cannot cancel job '{job_id}' in state '{current_state}'"
        )

    move_job(job_id, "canceled")


def mark_job_started(job_id: str) -> None:
    """
    Update started_at timestamp and move job to 'running'.
    Intended for dispatcher use.
    """
    job = load_job(job_id)
    job.mark_started(now_iso8601())

    # Overwrite file in current location before moving
    current_path = _find_job(job_id)
    if current_path is None:
        raise QueueError(f"Job '{job_id}' not found")

    try:
        current_path.write_text(job.to_yaml())
    except OSError as e:
        raise QueueError(f"Failed to update job '{job_id}': {e}")

    move_job(job_id, "running")


def mark_job_finished(job_id: str, success: bool) -> None:
    """
    Update finished_at timestamp and move job to 'finished' or 'failed'.
    Intended for dispatcher use.
    """
    job = load_job(job_id)
    job.mark_finished(now_iso8601())

    current_path = _find_job(job_id)
    if current_path is None:
        raise QueueError(f"Job '{job_id}' not found")

    try:
        current_path.write_text(job.to_yaml())
    except OSError as e:
        raise QueueError(f"Failed to update job '{job_id}': {e}")

    target_state = "finished" if success else "failed"
    move_job(job_id, target_state)
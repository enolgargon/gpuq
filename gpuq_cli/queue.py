from pathlib import Path
from typing import List, Optional
import os

from datetime import datetime, timedelta
from .jobs import Job
from .errors import QueueError
from .utils import now_iso8601, parse_iso8601


# -------------------------
# Configuration
# -------------------------

DEFAULT_SIGNALS_ROOT = Path("./signals")
SIGNALS_ROOT = Path(os.environ.get("GPUQ_SIGNALS_ROOT", DEFAULT_SIGNALS_ROOT))

DEFAULT_QUEUE_ROOT = Path("./queue")
QUEUE_ROOT = Path(os.environ.get("GPUQ_QUEUE_ROOT", DEFAULT_QUEUE_ROOT))

STATES = ["queued", "running", "finished", "failed", "canceled"]


# -------------------------
# Internal helpers
# -------------------------

def _resolve_job_id(prefix: str) -> str:
    """
    Resolve a job id from a prefix.
    The prefix must match exactly one job.
    """
    matches = []

    for state in STATES:
        state_dir = QUEUE_ROOT / state

        for file in state_dir.glob("*.yaml"):
            job_id = file.stem
            if job_id.startswith(prefix):
                matches.append(job_id)

    if not matches:
        raise QueueError(f"No job found matching '{prefix}'")

    if len(matches) > 1:
        raise QueueError(
            f"Ambiguous job id '{prefix}' (matches: {', '.join(matches)})"
        )

    return matches[0]

def _ensure_signals_structure() -> None:
    """
    Ensure that the signals root and cancel directory exist.
    """
    SIGNALS_ROOT.mkdir(parents=True, exist_ok=True)
    (SIGNALS_ROOT / "cancel").mkdir(exist_ok=True)


def _cancel_signal_path(job_id: str) -> Path:
    return SIGNALS_ROOT / "cancel" / job_id

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
                job.state = s
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
        job = Job.from_yaml(content)
        job.state = job_path.parent.name
        return job
    except Exception as e:
        raise QueueError(f"Failed to load job '{job_id}': {e}")


def cancel_job(job_id: str) -> None:
    """
    Request cancellation of a job by creating a cancel signal.
    """
    _ensure_queue_structure()
    _ensure_signals_structure()

    # Validate that job exists
    job_id = _resolve_job_id(job_id)
    current_path = _find_job(job_id)

    if current_path is None:
        raise QueueError(f"Job '{job_id}' not found")

    current_state = current_path.parent.name

    if current_state in ["finished", "failed", "canceled"]:
        raise QueueError(
            f"Cannot cancel job '{job_id}' in state '{current_state}'"
        )

    signal_path = _cancel_signal_path(job_id)

    if signal_path.exists():
        return

    try:
        signal_path.touch()
    except OSError as e:
        raise QueueError(
            f"Failed to create cancel signal for job '{job_id}': {e}"
        )


def garbage_collect(days: int = 14) -> int:
    _ensure_queue_structure()

    cutoff = datetime.utcnow() - timedelta(days=days)
    removable_states = ["finished", "failed", "canceled"]
    removed = 0

    for state in removable_states:
        state_dir = QUEUE_ROOT / state

        for job_file in state_dir.glob("*.yaml"):
            try:
                job = Job.from_yaml(job_file.read_text())

                if not job.finished_at:
                    continue

                finished = parse_iso8601(job.finished_at)

                if finished < cutoff:
                    job_file.unlink()
                    removed += 1

            except Exception:
                continue

    return removed
import argparse
from pathlib import Path
from typing import List

from .jobs import Job
from .queue import enqueue_job, list_jobs, cancel_job
from .utils import generate_job_id, get_current_user, now_iso8601
from .errors import JobValidationError, QueueError


# -------------------------
# CLI Parser
# -------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gpuq",
        description="Minimal GPU job queue CLI"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # submit
    submit_parser = subparsers.add_parser(
        "submit",
        help="Submit a new GPU job"
    )
    submit_parser.add_argument(
        "project",
        default=".",
        help="Path to project directory"
    )
    submit_parser.add_argument(
        "--compose",
        default="docker-compose.yml",
        help="Docker Compose file name (default: docker-compose.yml)"
    )
    submit_parser.add_argument(
        "--description",
        default="",
        help="Optional job description"
    )

    # list
    list_parser = subparsers.add_parser(
        "list",
        help="List jobs"
    )
    list_parser.add_argument(
        "--state",
        choices=["queued", "running", "finished", "failed", "canceled"],
        help="Filter jobs by state"
    )

    # cancel
    cancel_parser = subparsers.add_parser(
        "cancel",
        help="Cancel a job"
    )
    cancel_parser.add_argument(
        "job_id",
        help="ID of the job to cancel"
    )

    return parser


# -------------------------
# Command Handlers
# -------------------------

def handle_submit(args: argparse.Namespace) -> None:
    project_path = Path(args.project)

    if not project_path.exists():
        raise JobValidationError(
            f"Project path does not exist: {project_path}"
        )

    job = Job(
        job_id=generate_job_id(),
        user=get_current_user(),
        project_path=str(project_path.resolve()),
        compose_file=args.compose,
        created_at=now_iso8601(),
        description=args.description,
        started_at=None,
        finished_at=None,
    )

    enqueue_job(job)

    print(f"Job submitted successfully.")
    print(f"Job ID: {job.job_id}")


def handle_list(args: argparse.Namespace) -> None:
    jobs: List[Job] = list_jobs(state=args.state)

    if not jobs:
        print("No jobs found.")
        return

    for job in jobs:
        print(
            f"{job.job_id} | {job.user} | "
            f"{job.created_at} | "
            f"{job.description}"
        )


def handle_cancel(args: argparse.Namespace) -> None:
    cancel_job(args.job_id)
    print(f"Job '{args.job_id}' canceled.")


# -------------------------
# Dispatcher entry
# -------------------------

def dispatch(args: argparse.Namespace) -> None:
    if args.command == "submit":
        handle_submit(args)
    elif args.command == "list":
        handle_list(args)
    elif args.command == "cancel":
        handle_cancel(args)
    else:
        raise ValueError(f"Unknown command: {args.command}")
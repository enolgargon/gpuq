import argparse
from pathlib import Path
from typing import List

from .jobs import Job
from .queue import enqueue_job, list_jobs, cancel_job
from .utils import generate_job_id, get_current_user, now_iso8601, column_width, ensure_admin
from .errors import JobValidationError, QueueError
from . import __version__
from .colors import status, bold, warning


# -------------------------
# CLI Parser
# -------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gpuq",
        description="Minimal GPU job queue CLI"
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show gpuq version and exit"
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
        "-c",
        "--compose",
        default="docker-compose.yml",
        help="Docker Compose file name (default: docker-compose.yml)"
    )
    submit_parser.add_argument(
        "-d",
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
        "-s",
        "--state",
        choices=["queued", "running", "finished", "failed", "canceled"],
        help="Filter jobs by state"
    )
    list_parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Show all jobs (including finished/failed/canceled)"
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
    
    # admin
    admin_parser = subparsers.add_parser(
        "admin",
        help="Administrative commands"
    )

    admin_subparsers = admin_parser.add_subparsers(
        dest="admin_command",
        required=True
    )

    ## admin gc
    gc_parser = admin_subparsers.add_parser(
        "gc",
        help="Garbage collect old jobs"
    )

    gc_parser.add_argument(
        "--days",
        type=int,
        default=14,
        help="Delete jobs older than N days (default: 14)"
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

    jobs = []

    if args.state:
        jobs = list_jobs(state=args.state)

    elif args.all:
        jobs = list_jobs()

    else:
        jobs.extend(list_jobs("queued"))
        jobs.extend(list_jobs("running"))

    if not jobs:
        print(warning("No jobs found."))
        return

    id_width = column_width("JOB ID", [j.job_id for j in jobs])
    user_width = column_width("USER", [j.user for j in jobs])
    status_width = column_width("STATUS", [j.state for j in jobs])
    created_width = column_width("CREATED", [j.created_at for j in jobs])

    print(
        bold(f"{'JOB ID':<{id_width}} ")+
        bold(f"{'USER':<{user_width}} ")+
        bold(f"{'STATUS':<{status_width}} ")+
        bold(f"{'CREATED':<{created_width}} ")+
        bold(f"{'DESCRIPTION'}")
    )

    for job in jobs:
        print(
            f"{job.job_id:<{id_width}} "
            f"{job.user:<{user_width}} "
            f"{status(job.state):<{status_width}} "
            f"{job.created_at:<{created_width}} "
            f"{job.description}"
        )


def handle_cancel(args: argparse.Namespace) -> None:
    cancel_job(args.job_id)
    print(f"Job '{args.job_id}' canceled.")


def handle_admin(args: argparse.Namespace) -> None:
    if args.admin_command == "gc":
        handle_gc(args)
    else:
        raise ValueError(f"Unknown admin command: {args.command}")


def handle_gc(args: argparse.Namespace) -> None:
    ensure_admin()

    removed = garbage_collect(days=args.days)
    print(f"Removed {removed} old jobs.")


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
    elif args.command == "admin":
        handle_admin(args)
    else:
        raise ValueError(f"Unknown command: {args.command}")
from datetime import datetime
from typing import Optional
import getpass
import uuid
from .errors import QueueError
import os

ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def validate_iso8601(value: Optional[str], field_name: str) -> None:
    if value is None:
        return
    try:
        datetime.strptime(value, ISO_FORMAT)
    except ValueError:
        raise ValueError(
            f"Invalid ISO8601 timestamp for '{field_name}': {value}"
        )

def parse_iso8601(value: str) -> datetime:
    return datetime.strptime(value, ISO_FORMAT)


def now_iso8601() -> str:
    return datetime.utcnow().strftime(ISO_FORMAT)


def get_current_user() -> str:
    return getpass.getuser()


def generate_job_id() -> str:
    return f"{uuid.uuid4().hex[:8]}"

def column_width(header: str, values: list[str]) -> int:
    return max(len(header), *(len(v) for v in values))


def ensure_admin():
    if os.geteuid() != 0:
        raise QueueError("Admin command requires root privileges")
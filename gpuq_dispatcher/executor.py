import subprocess
import shlex
from typing import Optional

from .jobs import Job
from .errors import ExecutionError
from .config import (
    SYSTEMD_UNIT_PREFIX,
    DEFAULT_COMPOSE_FILE,
)

class JobExecutor:
    def __init__(self) -> None:
        pass

    def execute(self, job: Job) -> int:
        unit_name = self._unit_name(job)

        command = self._build_command(job)

        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
            )
        except Exception as e:
            raise ExecutionError(
                f"Failed to execute job {job.job_id}: {e}"
            ) from e

        return result.returncode

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _unit_name(self, job: Job) -> str:
        return f"{SYSTEMD_UNIT_PREFIX}-{job.job_id}"

    def _build_command(self, job: Job) -> list[str]:
        compose_file = job.compose_file or DEFAULT_COMPOSE_FILE

        docker_cmd = (
            f"docker compose -f {shlex.quote(compose_file)} up"
        )

        systemd_user_cmd = (
            f"systemd-run --user "
            f"--unit {unit_name} "
            f"--working-directory {shlex.quote(job.project_path)} "
            f"--collect --wait --pipe "
            f"bash -c {shlex.quote(docker_cmd)}"
        )

        return [
            "runuser",
            "-l",
            job.user,
            "-c",
            systemd_user_cmd,
        ]

    def is_unit_active(self, job: Job) -> bool:
        unit_name = self._unit_name(job)

        result = subprocess.run(
            ["systemctl", "is-active", unit_name],
            capture_output=True,
            text=True,
        )

        return result.stdout.strip() == "active"

    def get_unit_exit_code(self, job: Job) -> int:
        unit_name = self._unit_name(job)

        result = subprocess.run(
            [
                "systemctl",
                "show",
                unit_name,
                "--property=ExecMainStatus",
                "--value",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return 1  # assume failure if cannot retrieve

        try:
            return int(result.stdout.strip())
        except ValueError:
            return 1
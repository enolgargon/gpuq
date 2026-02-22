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

        systemd_cmd = [
            "systemd-run",
            "--user",
            "--unit",
            self._unit_name(job),
            "--working-directory",
            job.project_path,
            "--collect",
            "--wait",
            "--pipe",
            "bash",
            "-c",
            docker_cmd,
        ]

        return systemd_cmd
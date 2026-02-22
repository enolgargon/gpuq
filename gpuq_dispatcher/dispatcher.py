import time
from typing import Optional

from .config import POLL_INTERVAL, validate_config
from .queue import (
    get_queued_jobs,
    mark_job_running,
    mark_job_finished,
    mark_job_canceled,
)
from .scheduler import Scheduler
from .executor import JobExecutor
from .gpu_lock import GPULock
from .utils import setup_signal_handlers, sleep_interruptible, now_iso8601
from .errors import DispatcherError, QueueError, ExecutionError


class Dispatcher:
    def __init__(self) -> None:
        validate_config()

        self._scheduler = Scheduler()
        self._executor = JobExecutor()
        self._gpu_lock = GPULock()

        self._running = True

        setup_signal_handlers(self._request_shutdown)

    # ------------------------------------------------------------------
    # Lifecycle control
    # ------------------------------------------------------------------

    def _request_shutdown(self) -> None:
        self._running = False

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        while self._running:
            try:
                self._run_once()
            except DispatcherError as e:
                # In v1 we simply swallow dispatcher-level errors
                # to avoid stopping the whole service.
                # Proper logging will be added later.
                pass

            sleep_interruptible(POLL_INTERVAL, lambda: not self._running)

    def _run_once(self) -> None:
        queued_jobs = get_queued_jobs()

        job = self._scheduler.select_next_job(queued_jobs)

        if not job:
            return

        # ------------------------------------------------------------------
        # GPU-exclusive execution
        # ------------------------------------------------------------------

        with self._gpu_lock:
            started_at = now_iso8601()

            try:
                job = mark_job_running(job.job_id, started_at)
            except QueueError:
                # Job might have been canceled concurrently
                return

            try:
                exit_code = self._executor.execute(job)
                finished_at = now_iso8601()
                success = exit_code == 0
                mark_job_finished(job.job_id, finished_at, success)
            except ExecutionError:
                finished_at = now_iso8601()
                mark_job_finished(job.job_id, finished_at, success=False)

def main() -> None:
    dispatcher = Dispatcher()
    dispatcher.run()


if __name__ == "__main__":
    main()
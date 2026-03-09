import time
from typing import Optional

from .config import POLL_INTERVAL, validate_config
from .queue import (
    get_queued_jobs,
    mark_job_running,
    mark_job_finished,
    mark_job_canceled,
    get_running_jobs,
    get_cancel_requests,
    clear_cancel_request
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

    def _process_cancel_requests(self) -> None:
        cancel_requests = get_cancel_requests()

        if not cancel_requests:
            return

        running_jobs = {job.job_id: job for job in get_running_jobs()}

        for job_id in cancel_requests:

            if job_id in running_jobs:
                job = running_jobs[job_id]
                self._executor.stop_unit(job)

            try:
                mark_job_canceled(job_id)
            except QueueError:
                pass

            clear_cancel_request(job_id)

    def _process_signals(self) -> None:
        self._process_cancel_requests()

    def _reconcile_running_jobs(self) -> None:
        running_jobs = get_running_jobs()

        for job in running_jobs:
            if self._executor.is_unit_active(job):
                # Still running, nothing to do
                continue

            # Unit no longer active → retrieve exit code
            exit_code = self._executor.get_unit_exit_code(job)
            finished_at = now_iso8601()
            success = exit_code == 0

            mark_job_finished(job.job_id, finished_at, success)

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
        self._process_signals()
        self._reconcile_running_jobs()
        if get_running_jobs():
            return

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
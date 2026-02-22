from typing import List, Optional

from .jobs import Job
from .errors import SchedulerError


class Scheduler:
    def select_next_job(self, jobs: List[Job]) -> Optional[Job]:
        if not jobs:
            return None

        try:
            # FIFO: oldest job first
            return sorted(jobs, key=lambda job: job.created_at)[0]
        except Exception as e:
            raise SchedulerError(f"Failed to select next job: {e}") from e
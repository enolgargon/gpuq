import os
import fcntl

from .errors import GPULockError
from .config import GPU_LOCK_PATH


class GPULock:
    def __init__(self, lock_path: str = GPU_LOCK_PATH):
        self.lock_path = lock_path
        self._fd = None

    def acquire(self) -> None:
        if self._fd is not None:
            raise GPULockError("GPU lock already acquired")

        try:
            os.makedirs(os.path.dirname(self.lock_path), exist_ok=True)
            self._fd = open(self.lock_path, "w")
            fcntl.flock(self._fd, fcntl.LOCK_EX)
        except Exception as e:
            self._fd = None
            raise GPULockError(f"Failed to acquire GPU lock: {e}") from e

    def release(self) -> None:
        if self._fd is None:
            return

        try:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            self._fd.close()
        except Exception as e:
            raise GPULockError(f"Failed to release GPU lock: {e}") from e
        finally:
            self._fd = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
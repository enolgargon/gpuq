import os
import time
import signal
from typing import Callable, Optional


def sleep_interruptible(seconds: float, stop_flag: Callable[[], bool]) -> None:
    end = time.time() + seconds

    while time.time() < end:
        if stop_flag():
            return
        time.sleep(0.1)


def setup_signal_handlers(on_shutdown: Callable[[], None]) -> None:
    def handler(signum, frame):
        on_shutdown()

    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)


def ensure_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def is_process_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we don't have permission
        return True
    else:
        return True

def now_iso8601() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
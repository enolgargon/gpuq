import re
import time

import pytest

from gpuq_dispatcher.utils import (
    now_iso8601,
    sleep_interruptible,
)


# ------------------------------------------------------------------
# now_iso8601
# ------------------------------------------------------------------


def test_now_iso8601_returns_string():
    value = now_iso8601()
    assert isinstance(value, str)


def test_now_iso8601_format_is_valid_utc():
    value = now_iso8601()

    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
    assert re.match(pattern, value)


def test_now_iso8601_is_monotonic():
    t1 = now_iso8601()
    time.sleep(0.01)
    t2 = now_iso8601()

    assert t2 >= t1


# ------------------------------------------------------------------
# sleep_interruptible
# ------------------------------------------------------------------


def test_sleep_interruptible_completes_when_not_interrupted():
    start = time.time()

    sleep_interruptible(
        0.2,
        stop_flag=lambda: False,
    )

    elapsed = time.time() - start

    # Allow small timing tolerance
    assert elapsed >= 0.18


def test_sleep_interruptible_stops_early_when_flag_true():
    flag = {"stop": False}

    def stop_flag():
        return flag["stop"]

    def trigger_stop():
        time.sleep(0.05)
        flag["stop"] = True

    # Run trigger in background thread
    import threading

    t = threading.Thread(target=trigger_stop)
    t.start()

    start = time.time()
    sleep_interruptible(1.0, stop_flag=stop_flag)
    elapsed = time.time() - start

    t.join()

    # Should stop much earlier than full duration
    assert elapsed < 0.5
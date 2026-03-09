import os

from .errors import ConfigurationError


# -------------------------
# Queue configuration
# -------------------------

# Root directory of the filesystem-based job queue
QUEUE_ROOT = os.environ.get("GPUQ_QUEUE_ROOT", "./queue")
SIGNALS_ROOT = os.environ.get("GPUQ_SIGNALS_ROOT", "./signals")

# Subdirectories representing job states
QUEUE_STATES = [
    "queued",
    "running",
    "finished",
    "failed",
    "canceled",
]


# -------------------------
# Dispatcher behavior
# -------------------------

# Polling interval in seconds
POLL_INTERVAL = float(os.environ.get("GPUQ_POLL_INTERVAL", "2.0"))

if POLL_INTERVAL <= 0:
    raise ConfigurationError("GPUQ_POLL_INTERVAL must be greater than zero")


# -------------------------
# GPU lock configuration
# -------------------------

# Path used for GPU lock file
GPU_LOCK_PATH = os.environ.get(
    "GPUQ_GPU_LOCK_PATH",
    os.path.join(QUEUE_ROOT, ".gpu.lock"),
)


# -------------------------
# Execution configuration
# -------------------------

# Default Docker Compose file name
DEFAULT_COMPOSE_FILE = os.environ.get(
    "GPUQ_DEFAULT_COMPOSE_FILE",
    "docker-compose.yml",
)


# -------------------------
# systemd integration
# -------------------------

# Prefix used for systemd --user transient unit names
SYSTEMD_UNIT_PREFIX = os.environ.get(
    "GPUQ_SYSTEMD_UNIT_PREFIX",
    "gpuq-job",
)


# -------------------------
# Validation helper
# -------------------------

def validate_config() -> None:
    """
    Validate configuration consistency.
    This should be called once at dispatcher startup.
    """
    if not QUEUE_ROOT:
        raise ConfigurationError("QUEUE_ROOT is empty")

    if not isinstance(QUEUE_STATES, list) or not QUEUE_STATES:
        raise ConfigurationError("QUEUE_STATES must be a non-empty list")

    if POLL_INTERVAL <= 0:
        raise ConfigurationError("POLL_INTERVAL must be greater than zero")
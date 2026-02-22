class DispatcherError(Exception):
    """Base class for all dispatcher errors."""
    pass


class QueueError(DispatcherError):
    """Raised when queue operations fail."""
    pass


class SchedulerError(DispatcherError):
    """Raised when job scheduling fails."""
    pass


class ExecutionError(DispatcherError):
    """Raised when job execution fails."""
    pass


class GPULockError(DispatcherError):
    """Raised when acquiring or releasing the GPU lock fails."""
    pass


class ConfigurationError(DispatcherError):
    """Raised when dispatcher configuration is invalid."""
    pass
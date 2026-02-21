class GpuqError(Exception):
    """Base exception for gpuq."""
    pass


class JobValidationError(GpuqError):
    """Raised when a Job definition is invalid."""
    pass


class QueueError(GpuqError):
    """Raised when a queue operation fails."""
    pass
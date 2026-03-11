#!/usr/bin/env python3

import sys

from .cli import build_parser, dispatch
from .errors import GpuqError, JobValidationError, QueueError
from .colors import error

def main() -> int:
    parser = build_parser()

    try:
        args = parser.parse_args()
        dispatch(args)
        return 0

    except JobValidationError as e:
        print(error(f"Job validation error: {e}"), file=sys.stderr)
        return 2

    except QueueError as e:
        print(error(f"Queue error: {e}"), file=sys.stderr)
        return 3

    except GpuqError as e:
        print(error(f"gpuq error: {e}"), file=sys.stderr)
        return 4

    except KeyboardInterrupt:
        print(error("Interrupted by user."), file=sys.stderr)
        return 130

    except Exception as e:
        # Unexpected error: let it be visible
        print(error(f"Unexpected error: {e}"), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
# GPUQ

## NAME

gpuq - minimal GPU job queue for multi-user Linux servers

---

## SYNOPSIS

gpuq submit PROJECT_PATH [--compose FILE] [--description TEXT]

gpuq list [--state STATE]

gpuq cancel JOB_ID

---

## DESCRIPTION

gpuq is a minimal command-line interface for submitting, listing and
cancelling GPU jobs on a shared Linux server.

Jobs are persisted in a filesystem-based queue. The CLI does not execute
GPU workloads directly. Execution is delegated to a separate dispatcher
component.

gpuq guarantees:

- Persistent job registration
- Deterministic job identification
- Filesystem-level auditability
- Explicit state transitions

gpuq does not schedule or execute workloads by itself.

---

## COMMANDS

### submit

Submit a new GPU job to the queue.

The job is created in the "queued" state and awaits execution by the
dispatcher.

#### OPTIONS

PROJECT_PATH  
    Path to the project directory containing the workload.

--compose FILE  
    Docker Compose file to execute.  
    Default: docker-compose.yml

--description TEXT  
    Optional human-readable description of the job.

#### BEHAVIOR

- Generates a unique job identifier.
- Associates the job with the current system user.
- Records creation timestamp in ISO8601 format (UTC).
- Persists job metadata in the queue directory.

If the project path does not exist, the command fails.

#### EXAMPLE

gpuq submit ./experiment1 --description "baseline training"

---

### list

List jobs currently known to the queue.

By default, jobs across all states are listed.

#### OPTIONS

--state STATE  
    Filter jobs by state.

Valid states:

- queued
- running
- finished
- failed
- canceled

#### BEHAVIOR

Displays:

- Job ID
- Owner
- Creation timestamp
- Description

The command does not modify system state.

#### EXAMPLE

gpuq list
gpuq list --state queued

---

### cancel

Cancel a job.

If the job is in "queued" state, it is moved to "canceled".

If the job is currently "running", cancellation marks the job as canceled.
Actual termination of execution is handled by the dispatcher component.

#### PARAMETERS

JOB_ID  
    Identifier of the job to cancel.

#### BEHAVIOR

- Validates job existence.
- Validates current state.
- Updates job state in the filesystem queue.

Cancellation of jobs already in "finished", "failed" or "canceled"
state results in an error.

#### EXAMPLE

gpuq cancel job-1a2b3c4d

---

## ENVIRONMENT

GPUQ_QUEUE_ROOT  
    Root directory of the filesystem-based queue.  
    Default: ./queue

---

## EXIT STATUS

0   Success

2   Job validation error

3   Queue operation error

4   Internal gpuq error

130 Interrupted by user (SIGINT)

---

## FILES

The queue directory structure is:

QUEUE_ROOT/
    queued/
    running/
    finished/
    failed/
    canceled/

Each job is represented as a YAML file named:

JOB_ID.yaml

The state of a job is determined by the directory in which the file resides.

---

## DESIGN NOTES

- Job state is inferred from filesystem location.
- No database is used.
- No hidden state is maintained.
- The CLI performs no GPU execution.

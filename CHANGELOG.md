# Changelog

## v1.1.0 - 2026-03-11

### Added

- `gpuq --version` CLI option
- Short CLI flags (`-s`, `-a`, `-d`, etc.)
- Colored and styled terminal output when TTY is available
- Partial job ID matching for `gpuq cancel`
- `admin` subcommand for administrative operations
- `admin gc` command for garbage collection of old jobs
- Documentation for automated garbage collection via cron

### Changed

- Job ID format simplified (removed `job-` prefix)
- `gpuq list` now shows job state
- `gpuq list` now shows only `queued` and `running` jobs by default
- `--all` / `-a` flag added to show all jobs


## v1.0 - 2026-03-10

First stable release of gpuq.

### Features

- Filesystem-based GPU job queue
- CLI for job submission and management
- systemd-based dispatcher
- Docker rootless integration

### Documentation

- Complete documentation website
- Deployment and rollback procedures
- CLI reference
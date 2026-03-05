# gpuq

<img src="docs/imgs/gpuq.png" align="left" width="240px"/>

**gpuq** is a lightweight command-line tool designed to simplify GPU usage in shared computing environments. In many research labs and development servers, multiple users compete for a limited number of GPUs, often leading to manual coordination, inefficient utilization, or failed experiments when GPUs become unexpectedly occupied.

gpuq addresses this problem by providing a simple queue-based mechanism for launching GPU workloads. Instead of manually monitoring GPU availability, users can submit jobs and let gpuq automatically execute them as soon as resources become free. This makes it easier to run long experiment queues, automate training pipelines, and avoid conflicts between users sharing the same hardware.

The tool is intentionally minimal and easy to integrate into existing workflows. It works well with common deep learning frameworks and experiment pipelines, allowing researchers to focus on experimentation rather than resource management.

To help users adopt gpuq in modern reproducible environments, we also provide a **comprehensive documentation website** that explains how to integrate the tool with **Docker-based workflows**. The documentation includes practical guides for setting up GPU-enabled containers, adapting existing research pipelines, and using gpuq to schedule experiments inside containerized environments.

Full documentation and usage guides are available at:

👉 [https://enolgargon.github.io/gpuq-docs/](https://enolgargon.github.io/gpuq-docs/)

---

## Motivation

On shared Linux servers with a limited number of GPUs, it is common for multiple users to compete for the same GPU resources.  
Without coordination, this often leads to:

- Concurrent GPU usage causing performance degradation or failures
- Accidental oversubscription of GPU resources
- Incorrect file ownership when containers are executed with elevated privileges
- Lack of traceability regarding who executed what and when

`gpuq` aims to provide a **simple and transparent scheduling mechanism** for GPU workloads, without relying on heavyweight schedulers or external services.

---

## Scope and philosophy

This project is intentionally **minimalist** and follows a set of explicit design principles:

- **Docker rootless first**  
  All workloads are executed using Docker rootless to preserve correct UID/GID ownership of generated files.

- **Filesystem-based queue**  
  The job queue is implemented using the Linux filesystem as the source of truth. No databases or external services are required.

- **Single GPU, single job**  
  GPU access is explicitly serialized to guarantee exclusive usage.

- **Separation of responsibilities**  
  Job submission, scheduling, and execution are clearly separated components.

- **Auditability over opacity**  
  System-level auditing is preferred over hidden internal state.

- **Unix-aligned design**  
  The system relies on standard Linux mechanisms (filesystem permissions, systemd, auditd).

---

## What gpuq is NOT

It is important to explicitly state what this project does *not* try to be:

- It is **not** a full HPC scheduler (e.g. Slurm).
- It is **not** a Kubernetes replacement.
- It is **not** designed for hostile multi-tenant environments.
- It does **not** provide hard security isolation between malicious users.

The intended trust model is **cooperative users** on a shared system.

---

## Project Status

The initial prototype development phase of **gpuq** has been completed.

The core functionality — including the CLI, dispatcher, and filesystem-based queue mechanism — is now implemented and stable at the prototype level.

Current efforts are focused on:

- Real-world testing in multi-user environments
- Validation under realistic GPU workloads
- Deployment strategy refinement
- Operational hardening and usability improvements

The project is transitioning from prototype development to evaluation, integration, and practical adoption within the target environment.

---

## Running tests

Tests are executed using `pytest`. Since the project is not installed as a
Python package, the repository root must be added to `PYTHONPATH`.

To run the full test suite with coverage:

```bash
PYTHONPATH=$(pwd) pytest \
  --cov=gpuq_cli \
  --cov=gpuq_dispatcher \
  --cov-report=term-missing
```

Coverage reports focus on deterministic logic and filesystem-based components.
System-level execution (systemd, Docker, GPU access) is intentionally excluded
from unit tests.

---

## License

This project is licensed under the **gpuq Non-Commercial Share-Alike License (NC-SA) v1.0**.

In summary:

- Non-commercial use, modification, and redistribution are permitted.
- Attribution to the original author is mandatory.
- Derivative works must be distributed under the same license.
- Commercial use is **not permitted without explicit prior authorization** from the author.

See the `LICENSE` and `NOTICE` files for full details.

For commercial licensing inquiries, please contact the author directly.
# gpuq

`gpuq` is a minimal GPU job queue designed for multi-user Linux servers where GPU resources are scarce and shared between multiple users.

The project focuses on **serializing GPU usage**, **preserving correct file ownership**, and **providing auditability**, while remaining aligned with standard Linux tooling such as **Docker rootless** and **systemd --user**.

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


## Project status

⚠️ **Preliminary design and documentation phase**

At the current stage no production-ready implementation is available yet. Active work is focused on documentation and start de develop.

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
---
paths:
  - "**/*.py"
  - "**/*.pyi"
---

# Resource Lifecycle

- Acquire resources in context managers; `__exit__` and `finally` blocks must run on success, failure, and cancellation.
- `__exit__` must not swallow exceptions; return `None` by default; use `contextlib.suppress` only for narrowly scoped, intentional exception filtering.
- Shutdown order: unready → drain in-flight work → cancel remaining tasks → close pools; measure total time to fit the termination grace period.
- Document whether a managed resource remains usable after exit; test cleanup after success, raised exceptions, and early exit.
- Prefer `contextlib` and standard library helpers before custom lifecycle code; use `ExitStack` for dynamic or variable numbers of contexts.

---
paths:
  - "**/*.py"
  - "**/*.pyi"
---

# Error Handling

- Define a project exception taxonomy rooted in one base exception per package; translate third-party exceptions at boundaries with `raise ... from exc`.
- No bare `except:` or overly broad catches; catch specific exceptions only; suppress with context managers, not swallow-and-pass.
- Retries carry an explicit budget and exponential backoff with jitter; fail fast when the budget is exhausted.
- Log with `logger.exception()` exactly once at the boundary where the error is handled; preserve original exception context unless intentionally translating errors.
- Fail fast for programmer errors and invalid state; recover only from expected runtime failures with a documented recovery path.

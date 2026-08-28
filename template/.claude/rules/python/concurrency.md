---
paths:
  - "**/*.py"
  - "**/*.pyi"
---

# Concurrency

- Every task group, queue, pool, semaphore, or dynamic fan-out (no bare `asyncio.gather` over dynamic collections) must carry an explicit bound; unbounded workers exhaust memory and downstream capacity.
- All background work must propagate failures to the supervisor or caller; no fire-and-forget tasks without ownership.
- Structured task lifecycle: acquire → set timeouts → handle cancellation → clean up resources; ordered shutdown fits the termination grace period.
- Never block the event loop with synchronous I/O, sleeps, locks, or expensive computation; use `asyncio` for cooperative I/O only.
- Green-thread frameworks (gevent, eventlet) are banned; implicit context switches are hard to reason about and brittle across libraries.
- Document one-shot vs. reusable iterator contracts on public APIs that return iterators; test empty, single, large, and early-stop cases.

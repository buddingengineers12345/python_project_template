# Coding Style

- Line length: 100 characters (enforced by ruff formatter).
- Functions: one thing only; target ≤ 40 lines, hard limit 80 lines; McCabe complexity ≤ 10.
- Never silently swallow exceptions; no bare `except:` unless re-raising immediately.
- No magic values — replace bare literals with named constants or enums.
- No `print()` or debug variables in committed code; use structured logging.
- Comments explain *why*, not *what*. Use `TODO(username): description` for tracked work.

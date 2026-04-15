---
paths:
  - "**/*.sh"
  - "**/*.bash"
---

# Bash Security

- Never use `eval`; use `case` statements for dispatch.
- Pass arguments as separate words — never concatenate user input into a shell string.
- Validate all arguments and env vars before use; reject paths containing `..`.
- Use `mktemp` for temp files with `trap 'rm -f "$TMPFILE"' EXIT`.
- Hook scripts must only call trusted binaries (`uv`, `git`, `python3`, `ruff`); never `curl | bash`.

---
description: Run the full local CI pipeline (fix, fmt, lint, type, test) and report results. Use when the user asks to "run CI", "check everything", or verify the project before committing.
allowed-tools: Bash(just *)
---

Run the full local CI pipeline for this repository and report results.

Execute `just ci` which runs in this order:
1. `just fix` — auto-fix ruff lint issues
2. `just fmt` — ruff formatting
3. `just lint` — ruff lint check
4. `just type` — basedpyright type check
5. `just test` — pytest

After running, summarize:
- Which steps passed and which failed
- Any lint errors or type errors with file + line number
- Any failing test names and their assertion messages
- Suggested fixes for any failures

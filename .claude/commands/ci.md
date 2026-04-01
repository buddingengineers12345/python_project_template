Run the full local CI pipeline for this Copier template repository and report results.

Execute `just ci` which runs in this order:
1. `just fix` — auto-fix ruff lint issues
2. `just fmt` — ruff formatting
3. `just lint` — ruff lint check
4. `just type` — basedpyright type check
5. `just test` — pytest
6. `just precommit` — pre-commit on all files

After running, summarize:
- Which steps passed and which failed
- Any lint errors or type errors with file + line number
- Any failing test names and their assertion messages
- Suggested fixes for any failures

Run the full local CI pipeline for this Copier template repository and report results.

Execute `just ci` which runs in this order:
1. `just fix` — auto-fix ruff lint issues
2. `just fmt` — ruff formatting
3. `just ci-check` — read-only mirror of GitHub Actions, which runs:
   - `uv sync --frozen --extra dev`
   - `just fmt-check` — verify formatting (read-only)
   - `ruff check .` — lint
   - `basedpyright` — type check
   - `just docs-check` — docstring coverage (`--select D`)
   - `just test-ci` — pytest with coverage XML output
   - `pre-commit run --all-files --verbose`
   - `just audit` — pip-audit dependency security scan

After running, summarize:
- Which steps passed and which failed
- Any lint errors or type errors with file + line number
- Any failing test names and their assertion messages
- Any security vulnerabilities found by pip-audit
- Suggested fixes for any failures

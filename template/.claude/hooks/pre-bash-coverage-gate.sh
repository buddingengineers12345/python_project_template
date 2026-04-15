#!/usr/bin/env bash
# Claude PreToolUse hook — Bash
# Coverage gate: before git commit, run a quick coverage check and warn if
# coverage has dropped below the project threshold (default 85%).
#
# This is a non-blocking warning. The pre-commit hook and CI will enforce the
# hard gate — this hook gives earlier feedback so the developer can add missing
# tests before committing.
#
# Reference : Custom — project-specific hook, not derived from ECC.
# Exits     : 0 always (non-blocking; warnings on stderr only)

set -uo pipefail

INPUT=$(cat)

COMMAND=$(CLAUDE_HOOK_INPUT="$INPUT" python3 - <<'PYEOF'
import json, os

data = json.loads(os.environ["CLAUDE_HOOK_INPUT"])
print(data.get("tool_input", {}).get("command", ""))
PYEOF
) || { echo "$INPUT"; exit 0; }

# Only fire for git commit commands.
if ! echo "$COMMAND" | grep -qE '^\s*git\s+commit\b'; then
    echo "$INPUT"
    exit 0
fi

# Check if any staged Python files exist.
STAGED_PY=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null \
    | grep '\.py$' || true)

if [[ -z "$STAGED_PY" ]]; then
    echo "$INPUT"
    exit 0
fi

# Run the test suite with coverage (collect-only would not execute tests, so no
# coverage data would be produced). Non-zero exit from pytest is ignored; we
# parse the terminal report for TOTAL coverage.
echo "┌─ Coverage gate" >&2

# Note: do not hardcode the package path here; let the project's coverage config
# decide what is measured (e.g. src/ for generated projects, tests/ for this repo).
COV_OUTPUT=$(uv run --active pytest -q --cov --cov-report=term-missing \
    --cov-fail-under=85 2>&1 || true)

# Extract the total coverage percentage.
TOTAL_COV=$(echo "$COV_OUTPUT" | grep -oE 'TOTAL\s+[0-9]+\s+[0-9]+\s+([0-9]+)%' \
    | grep -oE '[0-9]+%$' || echo "")

if [[ -z "$TOTAL_COV" ]]; then
    # Could not determine coverage — skip silently.
    echo "│  Could not determine coverage — skipping check" >&2
    echo "└─" >&2
    echo "$INPUT"
    exit 0
fi

COV_NUM="${TOTAL_COV%\%}"

if [[ "$COV_NUM" -lt 85 ]]; then
    echo "│" >&2
    echo "│  ⚠  Coverage is ${TOTAL_COV} (threshold: 85%)" >&2
    echo "│  Consider adding tests before committing." >&2
    echo "│  Run \`just coverage\` to see which lines are uncovered." >&2
    echo "└─ ⚠  Coverage below threshold" >&2
else
    echo "│  Coverage: ${TOTAL_COV} ✓" >&2
    echo "└─ ✓ Coverage gate passed" >&2
fi

echo "$INPUT"
exit 0

#!/usr/bin/env bash
set -euo pipefail

TASK_ID="${1:?Usage: preflight.sh TASK_ID}"
TASK_FILE="tasks/${TASK_ID}.yaml"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Pre-flight checks for ${TASK_ID} ==="

# 1. Task file exists
if [[ ! -f "$TASK_FILE" ]]; then
    echo "FAIL: $TASK_FILE not found"
    exit 1
fi
echo "  [ok] Task file exists"

# 2. DoR validation
python3 "${SKILL_DIR}/validate_dor.py" "$TASK_FILE" > /dev/null
echo "  [ok] Definition of Ready met"

# 3. No uncommitted changes
if [[ -n "$(git status --porcelain)" ]]; then
    echo "FAIL: Uncommitted changes in working tree"
    echo "  Run: git stash or git commit"
    exit 1
fi
echo "  [ok] Working tree clean"

# 4. Base branch is up to date
BASE_BRANCH=$(python3 -c "import yaml; print(yaml.safe_load(open('$TASK_FILE'))['base_branch'])")
git fetch origin "$BASE_BRANCH" --quiet 2>/dev/null || true
LOCAL=$(git rev-parse "$BASE_BRANCH" 2>/dev/null || echo "none")
REMOTE=$(git rev-parse "origin/$BASE_BRANCH" 2>/dev/null || echo "none")
if [[ "$LOCAL" != "$REMOTE" ]]; then
    echo "WARN: $BASE_BRANCH is behind origin/$BASE_BRANCH"
    echo "  Run: git checkout $BASE_BRANCH && git pull"
fi
echo "  [ok] Base branch checked"

# 5. Target branch does not already exist (prevent stale work)
TARGET_BRANCH=$(python3 -c "import yaml; print(yaml.safe_load(open('$TASK_FILE'))['target_branch'])")
if git show-ref --verify --quiet "refs/heads/$TARGET_BRANCH" 2>/dev/null; then
    echo "WARN: Branch $TARGET_BRANCH already exists locally"
fi
echo "  [ok] Branch check done"

# 6. Python version check
REQUIRED_PYTHON=$(python3 -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    d = tomllib.load(f)
print(d.get('project', {}).get('requires-python', ''))
" 2>/dev/null || echo "")
ACTUAL_PYTHON=$(python3 --version | awk '{print $2}')
echo "  [ok] Python $ACTUAL_PYTHON (requires: $REQUIRED_PYTHON)"

# 7. Baseline CI passes
echo "  Running baseline CI (just ci)..."
if just ci > /dev/null 2>&1; then
    echo "  [ok] Baseline CI passes"
else
    echo "FAIL: Baseline CI does not pass on unmodified code"
    echo "  Fix baseline issues before starting new work"
    exit 1
fi

echo ""
echo "=== All pre-flight checks passed ==="

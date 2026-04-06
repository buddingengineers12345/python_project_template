#!/usr/bin/env bash
# Claude PostToolUse hook — Bash
# Log the PR URL and suggest review commands after gh pr create succeeds.
#
# Detects a GitHub pull request URL in the command output and surfaces
# it with a short set of follow-up commands so Claude can guide the user
# through the review flow without having to remember the exact gh invocations.
#
# Reference : https://github.com/affaan-m/everything-claude-code/blob/main/hooks/hooks.json
#             (hook id: post:bash:pr-created)
# Exits     : 0 always (PostToolUse hooks cannot block)

set -euo pipefail

INPUT=$(cat)

OUTPUT=$(python3 - <<'PYEOF'
import json, sys

data = json.loads(sys.stdin.read())
print(data.get("tool_output", {}).get("output", ""))
PYEOF
<<<"$INPUT") || exit 0

# Detect a GitHub PR URL in the command output
PR_URL=$(echo "$OUTPUT" \
    | grep -oE 'https://github\.com/[^/]+/[^/]+/pull/[0-9]+' \
    | head -1 || true)

if [[ -z "$PR_URL" ]]; then
    exit 0
fi

PR_NUM=$(echo "$PR_URL" | grep -oE '[0-9]+$' || true)

echo "┌─ Pull request created"
echo "│  URL: $PR_URL"
echo "│"
echo "│  Next steps:"
echo "│    gh pr view $PR_NUM --web        — open in browser"
echo "│    gh pr checks $PR_NUM            — CI status"
echo "│    gh pr diff $PR_NUM              — review diff"
echo "│"
echo "│  Once CI passes: gh pr merge $PR_NUM --squash"
echo "└─"

exit 0

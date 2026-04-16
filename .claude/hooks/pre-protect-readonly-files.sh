#!/usr/bin/env bash
# Claude PreToolUse hook — Write|Edit|MultiEdit
# Block direct edits to files listed in .claude/hooks/protected_files.csv.
#
# CSV format (.claude/hooks/protected_files.csv):
#   Column 1  (filepath)       — repo-relative path; hook matches on the basename
#   Column 4  (ai_can_modify)  — "never" triggers the block
#   Column 12 (reason)         — shown in the block message
#
# Rows starting with # are comments and are skipped.
# The header row (filepath,...) is also skipped.
#
# To protect a new file: add a row to .claude/hooks/protected_files.csv.
# To unprotect a file:   remove its row from that CSV.
# Never edit this hook script to manage the list.
#
# Exits: 0 = allow  |  2 = block
#
# Reference : Custom — project-specific hook, not derived from ECC.
# Exits     : 0 = allow  |  2 = block (protected file)

set -uo pipefail

INPUT=$(cat)

# Parse file_path from the JSON payload; pipe INPUT so heredoc/stdin don't conflict
FILE_PATH=$(printf '%s' "$INPUT" | python3 -c "
import json, os
data = json.loads(os.environ["CLAUDE_HOOK_INPUT"])
print(data.get('tool_input', {}).get('file_path', ''))
") || { printf '%s' "$INPUT"; exit 0; }

BASENAME=$(basename "$FILE_PATH")
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CSV="${REPO_ROOT}/.claude/hooks/protected_files.csv"

if [[ ! -f "$CSV" ]]; then
    # CSV missing — fail open so development is not blocked
    printf '%s' "$INPUT"
    exit 0
fi

# Parse CSV with Python; pipe CSV path as argument to avoid stdin conflicts
RESULT=$(python3 -c "
import csv, os, sys

basename = sys.argv[1]
csv_path = sys.argv[2]

try:
    with open(csv_path, newline='', encoding='utf-8') as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            row = next(csv.reader([stripped]))
            if not row:
                continue
            filepath_col = row[0].strip()
            if filepath_col == 'filepath':
                continue
            # column index 3 = ai_can_modify, index 11 = reason
            ai_can_modify = row[3].strip() if len(row) > 3 else ''
            reason = row[11].strip() if len(row) > 11 else 'Protected — human review required'
            if os.path.basename(filepath_col) == basename and ai_can_modify == 'never':
                print('BLOCK:' + reason)
                sys.exit(0)
    print('ALLOW')
except Exception:
    print('ALLOW')
" "$BASENAME" "$CSV") || RESULT="ALLOW"

if [[ "$RESULT" == BLOCK:* ]]; then
    REASON="${RESULT#BLOCK:}"
    printf '┌─ BLOCKED: Direct edit to protected file: %s\n' "$BASENAME" >&2
    printf '│\n' >&2
    printf '│  %s\n' "$REASON" >&2
    printf '│\n' >&2
    printf '│  To modify this file, edit it manually outside this AI session\n' >&2
    printf '│  and commit via the normal review process.\n' >&2
    printf '│\n' >&2
    printf '│  To change the protected-files list, edit (with human review):\n' >&2
    printf '│    .claude/hooks/protected_files.csv\n' >&2
    printf '└─\n' >&2
    exit 2
fi

printf '%s' "$INPUT"

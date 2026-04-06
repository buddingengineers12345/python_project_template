#!/usr/bin/env bash
# Claude PreToolUse hook — Write|Edit|MultiEdit
# Protect linter and type-checker configuration from weakening edits.
#
# Monitors edits to pyproject.toml, pyproject.toml.jinja, and
# .pre-commit-config.yaml. BLOCKS clearly weakening changes; WARNS on
# modifications to ruff lint rule sections so they are not overlooked.
#
# BLOCK conditions:
#   - typeCheckingMode = "off" or "basic"  (downgrade from strict / standard)
#   - Core ruff rule category added to ignore list: D, E, F, I, B
#
# WARN conditions:
#   - Any edit that touches [tool.ruff.lint] select/ignore in pyproject.toml
#
# The intent is to steer Claude toward fixing code rather than suppressing
# diagnostics. Legitimate additions (dependencies, metadata) pass freely.
#
# Reference : https://github.com/affaan-m/everything-claude-code/blob/main/hooks/hooks.json
#             (hook id: pre:config-protection)
# Exits     : 0 = allow  |  2 = block

set -uo pipefail

INPUT=$(cat)

# Extract file path first (used in error message for the BLOCK case)
FILE_PATH=$(python3 - <<'PYEOF'
import json, sys

data = json.loads(sys.stdin.read())
print(data.get("tool_input", {}).get("file_path", ""))
PYEOF
<<<"$INPUT") || { echo "$INPUT"; exit 0; }

BASENAME=$(basename "$FILE_PATH")

# Only check protected config files
case "$BASENAME" in
    pyproject.toml|pyproject.toml.jinja|.pre-commit-config.yaml) ;;
    *) echo "$INPUT"; exit 0 ;;
esac

# Run protection analysis; outputs: OK | SKIP | BLOCK:<reason> | WARN:<reason>
CHECK=$(python3 - <<'PYEOF'
import json, re, sys

data = json.loads(sys.stdin.read())
new_content = (
    data.get("tool_input", {}).get("new_string", "")
    or data.get("tool_input", {}).get("content", "")
)

file_path = data.get("tool_input", {}).get("file_path", "")
basename = file_path.rsplit("/", 1)[-1] if "/" in file_path else file_path

if not new_content:
    print("SKIP")
    sys.exit(0)

# ── Blocking: typeCheckingMode downgrade ─────────────────────────────────────
if re.search(r'typeCheckingMode\s*=\s*"(off|basic)"', new_content):
    print('BLOCK:typeCheckingMode downgraded to "off" or "basic" — must remain "standard" or "strict"')
    sys.exit(0)

# ── Blocking: core ruff rules silenced ───────────────────────────────────────
ignore_match = re.search(r'ignore\s*=\s*\[([^\]]*)\]', new_content, re.DOTALL)
if ignore_match:
    ignore_block = ignore_match.group(1)
    for rule in ("D", "E", "F", "I", "B"):
        if re.search(rf'["\x27]{re.escape(rule)}["\x27]', ignore_block):
            print(f'BLOCK:Core ruff rule "{rule}" added to ignore list — fix code instead of suppressing rules')
            sys.exit(0)

# ── Warning: ruff lint section modified ──────────────────────────────────────
if basename in ("pyproject.toml", "pyproject.toml.jinja"):
    if (
        re.search(r'\[tool\.ruff\.lint\]', new_content)
        and re.search(r'(?:select|ignore)\s*=', new_content)
    ):
        print("WARN:Modifying [tool.ruff.lint] select/ignore rules — verify standards are not weakened")
        sys.exit(0)

print("OK")
PYEOF
<<<"$INPUT") || { echo "$INPUT"; exit 0; }

case "$CHECK" in
    BLOCK:*)
        REASON="${CHECK#BLOCK:}"
        echo "┌─ BLOCKED: Config protection" >&2
        echo "│" >&2
        echo "│  File  : $FILE_PATH" >&2
        echo "│  Issue : $REASON" >&2
        echo "│" >&2
        echo "│  Correct approach: fix code to comply with quality standards," >&2
        echo "│  rather than weakening the configuration to suppress diagnostics." >&2
        echo "│" >&2
        echo "│    just fix   — auto-fix ruff violations" >&2
        echo "│    just lint  — list remaining issues" >&2
        echo "│    just type  — list type errors" >&2
        echo "└─" >&2
        exit 2
        ;;
    WARN:*)
        REASON="${CHECK#WARN:}"
        echo "┌─ Config change notice" >&2
        echo "│  $REASON" >&2
        echo "│  Ensure quality standards (ruff rules, complexity limits) are not reduced." >&2
        echo "└─" >&2
        ;;
esac

echo "$INPUT"

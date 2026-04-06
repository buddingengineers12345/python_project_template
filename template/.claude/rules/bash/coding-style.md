# Bash / Shell Coding Style

# applies-to: **/*.sh

Shell scripts in this project live under `.claude/hooks/` and `scripts/`.

## Shebang and strict mode

```bash
#!/usr/bin/env bash
set -euo pipefail
```

For scripts that must not exit non-zero accidentally (e.g. PreToolUse hooks):
```bash
set -uo pipefail   # intentionally NOT -e
```

## Variable quoting

Always quote variable expansions:

```bash
# Correct
if [[ -f "$file_path" ]]; then ...

# Wrong — breaks on paths with spaces
if [[ -f $file_path ]]; then ...
```

Use `[[ ]]` (bash conditionals), not `[ ]` (POSIX test).

## Reading stdin (hook scripts)

```bash
INPUT=$(cat)

FILE_PATH=$(python3 - <<'PYEOF'
import json, sys
data = json.loads(sys.stdin.read())
print(data.get("tool_input", {}).get("file_path", ""))
PYEOF
<<<"$INPUT") || { echo "$INPUT"; exit 0; }
```

## Output formatting

```bash
echo "┌─ Hook name: $context"
echo "│  Informational content"
echo "└─ ✓ Done"
```

PostToolUse / Stop / SessionStart: print to **stdout**.
PreToolUse blocking messages: print to **stderr**.

## Exit codes

Only PreToolUse hooks should exit 2 (block). All other hooks must exit 0.

When allowing a PreToolUse tool call to proceed, echo `$INPUT` back to stdout:

```bash
echo "$INPUT"
exit 0
```

## Functions

```bash
check_python_file() {
    local file_path="$1"
    [[ "$file_path" == *.py ]] && [[ -f "$file_path" ]]
}
```

## Portability

Hooks run on macOS and Linux. Avoid GNU-specific flags when a POSIX alternative exists.

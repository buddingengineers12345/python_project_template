# Bash / Shell Coding Style

# applies-to: **/*.sh

Shell scripts in this repository are hook scripts under `.claude/hooks/` and helper
scripts under `scripts/`. These rules apply to all `.sh` files.

## Shebang and strict mode

Every script must start with the appropriate shebang and enable strict mode:

```bash
#!/usr/bin/env bash
# One-line description of what this script does.
```

For PostToolUse / Stop / SessionStart hooks (non-blocking):

```bash
set -euo pipefail
```

For PreToolUse blocking hooks (must not exit non-zero accidentally):

```bash
set -uo pipefail   # intentionally NOT -e; we handle exit codes manually
```

`-e` (exit on error), `-u` (error on unset variable), `-o pipefail` (pipe failures propagate).
Document clearly when `-e` is omitted and why.

## Variable quoting

Always quote variable expansions unless you intentionally want word splitting:

```bash
# Correct
file_path="$1"
if [[ -f "$file_path" ]]; then ...

# Wrong — breaks on paths with spaces
if [[ -f $file_path ]]; then ...
```

Use `[[ ]]` (bash conditionals) instead of `[ ]` (POSIX test). `[[ ]]` handles
spaces in variables without quoting issues.

## Reading stdin (hook scripts)

Hook scripts receive JSON on stdin. Always capture it immediately and parse with Python:

```bash
INPUT=$(cat)

FILE_PATH=$(python3 - <<'PYEOF'
import json, sys
data = json.loads(sys.stdin.read())
print(data.get("tool_input", {}).get("file_path", ""))
PYEOF
<<<"$INPUT") || { echo "$INPUT"; exit 0; }
```

The `|| { echo "$INPUT"; exit 0; }` guard ensures that a malformed JSON payload never
accidentally blocks a PreToolUse hook.

## Output formatting

Use box-drawing characters for structured output (consistent with all other hooks):

```bash
echo "┌─ Hook name: $context"
echo "│"
echo "│  Informational content"
echo "└─ ✓ Done"   # or  └─ ✗ Fix before committing
```

- PostToolUse / Stop / SessionStart hooks: print to **stdout**.
- PreToolUse blocking messages: print to **stderr** (shown to the user on block).

## Exit codes

| Script type | Exit 0 | Exit 2 |
|-------------|--------|--------|
| PreToolUse | Allow tool to proceed | Block tool call |
| PostToolUse | Normal completion | Not meaningful — avoid |
| Stop / SessionStart | Normal completion | Not meaningful — avoid |

Only PreToolUse hooks should ever exit 2. All other hooks must exit 0.

When a PreToolUse hook allows the call to proceed, echo `$INPUT` back to stdout (required):

```bash
echo "$INPUT"   # pass-through: required for the tool call to proceed
exit 0
```

## Naming and file organisation

File naming convention:
```
{event-prefix}-{matcher}-{purpose}.sh
```

| Prefix | Lifecycle event |
|--------|----------------|
| `pre-bash-` | PreToolUse on Bash |
| `pre-write-` | PreToolUse on Write |
| `pre-config-` | PreToolUse on Edit/Write/MultiEdit |
| `pre-protect-` | PreToolUse guard for a specific resource |
| `post-edit-` | PostToolUse on Edit or Write |
| `post-bash-` | PostToolUse on Bash |
| `session-` | SessionStart |
| `stop-` | Stop |

## Functions

Extract repeated logic into shell functions. Name functions in `snake_case`:

```bash
check_python_file() {
    local file_path="$1"
    [[ "$file_path" == *.py ]] && [[ -f "$file_path" ]]
}
```

Keep functions short (≤ 30 lines). Scripts that grow beyond ~100 lines should be
split into multiple files or rewritten as Python.

## Portability

Hook scripts run on macOS and Linux. Avoid GNU-specific flags when a POSIX-compatible
alternative exists. Test both platforms if in doubt.

Copier `_tasks` use `/bin/sh` (POSIX shell, not bash). Use `#!/bin/sh` and POSIX-only
syntax in tasks embedded in `copier.yml`.

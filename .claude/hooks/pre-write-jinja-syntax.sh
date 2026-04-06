#!/usr/bin/env bash
# Claude PreToolUse hook — Write
# Validate Jinja2 syntax BEFORE writing a new or overwritten .jinja template file.
#
# This is the pre-Write counterpart to the post-Edit Jinja2 syntax check. Firing
# BEFORE the file is written (exit 2 = block) prevents committing a malformed
# template that would fail silently at `copier copy` time — often far from the
# point of introduction.
#
# Uses the same Jinja2 extensions that Copier enables in copier.yml:
#   - jinja2_time.TimeExtension  ({% now %} expressions)
#   - jinja2.ext.do              ({% do %} statement)
#   - jinja2.ext.loopcontrols    ({% break %}, {% continue %})
#
# For Edit operations on existing .jinja files, post-edit-jinja.sh provides the
# post-edit non-blocking check as a secondary layer.
#
# Reference : Custom — project-specific hook, not derived from ECC.
#             Upgrades post-edit-jinja.sh from warn-after to block-before for Write.
# Exits     : 0 = allow  |  2 = block

set -uo pipefail

INPUT=$(cat)

FILE_PATH=$(python3 - <<'PYEOF'
import json, sys

data = json.loads(sys.stdin.read())
print(data.get("tool_input", {}).get("file_path", ""))
PYEOF
<<<"$INPUT") || { echo "$INPUT"; exit 0; }

# Only process .jinja files
if [[ "$FILE_PATH" != *.jinja ]] || [[ -z "$FILE_PATH" ]]; then
    echo "$INPUT"
    exit 0
fi

# Extract the file content from tool_input.content
CONTENT=$(python3 - <<'PYEOF'
import json, sys

data = json.loads(sys.stdin.read())
print(data.get("tool_input", {}).get("content", ""))
PYEOF
<<<"$INPUT") || { echo "$INPUT"; exit 0; }

if [[ -z "$CONTENT" ]]; then
    echo "$INPUT"
    exit 0
fi

# Validate the Jinja2 syntax with the same extensions Copier uses
RESULT=$(python3 - <<'PYEOF'
import sys

content = sys.argv[1] if len(sys.argv) > 1 else ""

try:
    from jinja2 import Environment, TemplateSyntaxError

    extensions = ["jinja2.ext.do", "jinja2.ext.loopcontrols"]
    try:
        extensions.insert(0, "jinja2_time.TimeExtension")
    except Exception:
        pass  # jinja2_time not installed; skip — Copier will catch it

    env = Environment(extensions=extensions)  # noqa: S701
    env.parse(content)
    print("OK")

except TemplateSyntaxError as exc:
    print(f"ERROR:line {exc.lineno}: {exc.message}")

except ImportError as exc:
    print(f"SKIP:Jinja2 not importable: {exc}")
PYEOF
"$CONTENT") || { echo "$INPUT"; exit 0; }

case "$RESULT" in
    OK)
        ;;
    ERROR:*)
        DETAIL="${RESULT#ERROR:}"
        echo "┌─ BLOCKED: Jinja2 syntax error in $FILE_PATH" >&2
        echo "│" >&2
        echo "│  $DETAIL" >&2
        echo "│" >&2
        echo "│  Fix the template syntax before writing." >&2
        echo "│  This file would fail at 'copier copy' time with the same error." >&2
        echo "└─" >&2
        exit 2
        ;;
    SKIP:*)
        # Could not import Jinja2 — allow the write and let post-edit hook catch it
        ;;
esac

echo "$INPUT"

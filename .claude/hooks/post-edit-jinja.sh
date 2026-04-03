#!/usr/bin/env bash
# Claude PostToolUse hook — runs after any Edit or Write tool call.
#
# If the edited file is a Jinja2 (.jinja) template, this hook verifies
# that the template parses without syntax errors using the same Jinja2
# extensions that Copier enables (jinja2_time, do, loopcontrols).
#
# Output is surfaced to Claude so syntax errors are caught immediately,
# not at `copier copy` time. Always exits 0 (non-blocking feedback).

set -euo pipefail

INPUT=$(cat)

FILE_PATH=$(python3 - <<'PYEOF'
import json, sys

data = json.loads(sys.stdin.read())
print(data.get("tool_input", {}).get("file_path", ""))
PYEOF
<<<"$INPUT")

if [[ "$FILE_PATH" != *.jinja ]] || [[ -z "$FILE_PATH" ]] || [[ ! -f "$FILE_PATH" ]]; then
    exit 0
fi

echo "┌─ Jinja2 syntax check: $FILE_PATH"

python3 - "$FILE_PATH" <<'PYEOF'
import sys
from pathlib import Path

file_path = Path(sys.argv[1])
content = file_path.read_text(encoding="utf-8")

try:
    from jinja2 import Environment, TemplateSyntaxError

    # Mirror the extensions Copier enables in copier.yml
    extensions = ["jinja2.ext.do", "jinja2.ext.loopcontrols"]
    try:
        extensions.insert(0, "jinja2_time.TimeExtension")
    except Exception:
        pass  # jinja2_time not available; skip it

    env = Environment(extensions=extensions)  # noqa: S701
    env.parse(content)
    print("│  ✓ Jinja2 syntax OK")

except TemplateSyntaxError as exc:
    print(f"│  ✗ Syntax error at line {exc.lineno}: {exc.message}")
    print("│")
    print("└─ Fix template syntax before committing")
    sys.exit(0)  # exit 0 so hook is non-blocking; output is the feedback

except ImportError as exc:
    print(f"│  ⚠ Could not import Jinja2: {exc}")
PYEOF

echo "└─ Done"
exit 0

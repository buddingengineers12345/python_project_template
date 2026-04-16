# File Locking Implementation Plan (Claude Code only)

> **Audience:** A junior model (Haiku) executing the steps below.
> **Source repo:** `/Users/kzqr495/Documents/workspace/python_project_template`
> **Goal:** Prevent AI agents from modifying stable files without explicit user intent.
> **Approach:** Defense in depth using only Claude Code's native mechanisms — no external
> tools, no git pre-receive hooks, no CODEOWNERS automation.

## How to use this document

1. Read the entire document before touching files.
2. Execute the phases in order. Each phase is independently committable.
3. After every phase, run the validation block. If validation fails, STOP and report.
4. Conventional Commit format for every commit.
5. Do not skip Phase 0 (manifest) — every later phase depends on it.

## Conceptual model — what we are building

Three layers of protection backed by **one manifest**:

```
.claude/locked-files.txt          ← single source of truth (one path/glob per line)
        │
        ├── consumed by hook   →  .claude/hooks/pre-write-locked-files.sh   (Write|Edit|MultiEdit)
        ├── consumed by hook   →  .claude/hooks/pre-bash-locked-files.sh    (Bash redirects)
        ├── synced into        →  .claude/settings.json  permissions.deny   (hard block)
        └── documented in      →  CLAUDE.md  "Locked files" section          (model-side guidance)
```

Bypass protocol: setting the environment variable `CLAUDE_UNLOCK=<path-or-glob>` before
the session disables the hooks for that path only. The `permissions.deny` layer is
intentionally NOT bypassable by env var — those paths require editing `settings.json`.

Tiers:

- **Tier 1 (HARD LOCK):** in manifest with prefix `!` → blocked by both hook and `permissions.deny`.
- **Tier 2 (SOFT LOCK):** in manifest without prefix → hook warns + may block on weakening
  patterns; not in `permissions.deny`.
- **Tier 3 (FREE):** not in manifest at all.

---

## Phase 0 — Working branch and manifest

### 0.1 Branch

```bash
git checkout -b chore/file-locking-claude-code
```

### 0.2 Create the manifest

Write `.claude/locked-files.txt` with the following exact contents. Lines starting with
`#` are comments. Lines starting with `!` are Tier 1 (hard lock). All other non-blank
lines are Tier 2 (soft lock). Glob syntax follows shell globbing (`**` recursive).

```text
# ============================================================================
# .claude/locked-files.txt
#
# Single source of truth for file-locking. Consumed by:
#   - .claude/hooks/pre-write-locked-files.sh
#   - .claude/hooks/pre-bash-locked-files.sh
#   - .claude/settings.json permissions.deny (synced via `just lock-sync`)
#
# Format:
#   #         comment
#   !path     TIER 1: hard lock (hook block + permissions.deny)
#   path      TIER 2: soft lock (hook warn / weakening detection only)
#
# Globs use shell syntax. ** matches any number of directories.
# Bypass: set CLAUDE_UNLOCK=<path> before the session (Tier 2 hook only).
# ============================================================================

# ---------- Tier 1: legal & lockfiles ----------
!LICENSE
!template/LICENSE.jinja
!uv.lock
!.secrets.baseline

# ---------- Tier 1: repo integrity ----------
!.gitignore
!.gitmessage
!.pre-commit-config.yaml

# ---------- Tier 1: CI configuration ----------
!.github/workflows/**
!template/.github/workflows/**
!.github/dependabot.yml
!.github/CODEOWNERS

# ---------- Tier 1: meta-lock (locking the locks) ----------
!.claude/settings.json
!.claude/locked-files.txt
!.claude/hooks/pre-write-locked-files.sh
!.claude/hooks/pre-bash-locked-files.sh
!.claude/hooks/pre-protect-uv-lock.sh
!.claude/hooks/pre-config-protection.sh
!template/.claude/settings.json

# ---------- Tier 2: project configuration (weakening already blocked elsewhere) ----------
pyproject.toml
copier.yml
justfile
template/justfile.jinja

# ---------- Tier 2: standards docs (rules of the road) ----------
.claude/rules/**/*.md
template/.claude/rules/**/*.md
.claude/commands/**/*.md
template/.claude/commands/**/*.md.jinja
.claude/CLAUDE.md

# ---------- Tier 2: generated-project surface ----------
template/CLAUDE.md.jinja
template/README.md.jinja
template/pyproject.toml.jinja
template/{{_copier_conf.answers_file}}.jinja
```

Validation:

```bash
test -f .claude/locked-files.txt && echo OK
grep -c '^!' .claude/locked-files.txt    # expect ~20 hard locks
grep -cv '^#\|^!\|^$' .claude/locked-files.txt  # expect ~10 soft locks
```

---

## Phase 1 — The Tier-1 + Tier-2 hook (Write/Edit/MultiEdit)

### 1.1 Create `.claude/hooks/pre-write-locked-files.sh`

This hook reads the manifest, matches `tool_input.file_path` against each entry, and
either blocks or warns based on the tier prefix.

Write this exact content:

```bash
#!/usr/bin/env bash
# pre-write-locked-files.sh
# PreToolUse hook for Write|Edit|MultiEdit. Blocks edits to locked paths.
#
# Manifest: .claude/locked-files.txt
#   !path  → block (Tier 1)
#   path   → warn  (Tier 2)
#
# Bypass: CLAUDE_UNLOCK=<exact-path-or-glob> allows that single entry through.
# Tier 1 entries can also be bypassed via the env var, but should normally
# require editing .claude/settings.json (which is itself Tier 1).

set -uo pipefail

INPUT=$(cat)

FILE_PATH=$(python3 - <<'PYEOF' <<<"$INPUT"
import json, sys
try:
    data = json.loads(sys.stdin.read())
    print(data.get("tool_input", {}).get("file_path", ""))
except Exception:
    print("")
PYEOF
) || { echo "$INPUT"; exit 0; }

# No path → nothing to check → pass through.
if [[ -z "$FILE_PATH" ]]; then
    echo "$INPUT"
    exit 0
fi

MANIFEST=".claude/locked-files.txt"
if [[ ! -f "$MANIFEST" ]]; then
    echo "$INPUT"
    exit 0
fi

# Normalise to a path relative to repo root.
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
REL_PATH="${FILE_PATH#$REPO_ROOT/}"

match_glob() {
    # $1 = glob pattern, $2 = path → 0 if match, 1 if not
    local pattern="$1" path="$2"
    case "$path" in
        $pattern) return 0 ;;
        *) return 1 ;;
    esac
}

UNLOCK="${CLAUDE_UNLOCK:-}"

while IFS= read -r line; do
    # Skip comments and blanks.
    [[ -z "$line" || "$line" =~ ^# ]] && continue

    tier="soft"
    pattern="$line"
    if [[ "$line" == !* ]]; then
        tier="hard"
        pattern="${line#!}"
    fi

    if match_glob "$pattern" "$REL_PATH"; then
        # Bypass check.
        if [[ -n "$UNLOCK" ]] && match_glob "$UNLOCK" "$REL_PATH"; then
            echo "┌─ Locked-file bypass: $REL_PATH" >&2
            echo "│  Matched manifest entry: $line" >&2
            echo "│  Allowed by CLAUDE_UNLOCK=$UNLOCK" >&2
            echo "└─ Proceeding (bypass active)" >&2
            echo "$INPUT"
            exit 0
        fi

        if [[ "$tier" == "hard" ]]; then
            echo "┌─ Locked-file BLOCK: $REL_PATH" >&2
            echo "│  Matched Tier 1 entry: $line" >&2
            echo "│  This file is hard-locked. To edit it:" >&2
            echo "│    1. Confirm the change is intentional with the user." >&2
            echo "│    2. Re-run with CLAUDE_UNLOCK='$pattern' set in the environment." >&2
            echo "│    3. Or remove/edit the entry in .claude/locked-files.txt" >&2
            echo "│       (which is itself locked — requires CLAUDE_UNLOCK)." >&2
            echo "└─ ✗ Edit blocked" >&2
            exit 2
        else
            # Tier 2 — warn but allow.
            echo "┌─ Locked-file WARN: $REL_PATH" >&2
            echo "│  Matched Tier 2 entry: $line" >&2
            echo "│  This file is semi-stable. Confirm the change is intentional." >&2
            echo "│  Set CLAUDE_UNLOCK='$pattern' to silence this warning." >&2
            echo "└─ ⚠ Proceeding with warning" >&2
            echo "$INPUT"
            exit 0
        fi
    fi
done < "$MANIFEST"

# No match.
echo "$INPUT"
exit 0
```

Make it executable:

```bash
chmod +x .claude/hooks/pre-write-locked-files.sh
```

### 1.2 Quick smoke test

Simulate a Tier-1 block:

```bash
echo '{"tool_input": {"file_path": "'"$(pwd)"'/LICENSE"}}' \
  | bash .claude/hooks/pre-write-locked-files.sh
echo "exit=$?"
# Expect: stderr contains "Locked-file BLOCK: LICENSE", exit=2
```

Simulate a Tier-2 warn:

```bash
echo '{"tool_input": {"file_path": "'"$(pwd)"'/justfile"}}' \
  | bash .claude/hooks/pre-write-locked-files.sh
echo "exit=$?"
# Expect: stderr contains "Locked-file WARN: justfile", exit=0
```

Simulate a free path:

```bash
echo '{"tool_input": {"file_path": "'"$(pwd)"'/docs/notes.md"}}' \
  | bash .claude/hooks/pre-write-locked-files.sh
echo "exit=$?"
# Expect: no stderr, exit=0
```

Simulate the bypass:

```bash
CLAUDE_UNLOCK='LICENSE' bash -c '
  echo "{\"tool_input\": {\"file_path\": \"'"$(pwd)"'/LICENSE\"}}" \
    | bash .claude/hooks/pre-write-locked-files.sh
'
# Expect: stderr "bypass active", exit=0
```

If any of the four cases above behaves differently, fix the hook before continuing. Most
likely cause: shell glob matching is locale-sensitive — make sure `shopt -s extglob` is
not required. The script uses POSIX `case` matching on purpose.

---

## Phase 2 — The Bash redirect hook

### 2.1 Why a second hook

The Write/Edit/MultiEdit hook does NOT fire when the model writes a file via Bash:

```bash
cat > LICENSE <<EOF        # bypasses Write hook entirely
sed -i 's/MIT/GPL/' LICENSE
```

This hook scans Bash commands for redirects and in-place edits targeting locked paths.

### 2.2 Create `.claude/hooks/pre-bash-locked-files.sh`

```bash
#!/usr/bin/env bash
# pre-bash-locked-files.sh
# PreToolUse hook for Bash. Blocks shell commands that write to locked paths.
#
# Detects:
#   - cat > FILE / cat >> FILE
#   - tee FILE / tee -a FILE
#   - sed -i ... FILE
#   - perl -i ... FILE
#   - python -c '... open(FILE, "w") ...'   (best-effort regex)
#   - cp/mv SOURCE FILE
#   - > FILE / >> FILE  (any redirect)
#
# Manifest and bypass behaviour identical to pre-write-locked-files.sh.

set -uo pipefail

INPUT=$(cat)

CMD=$(python3 - <<'PYEOF' <<<"$INPUT"
import json, sys
try:
    data = json.loads(sys.stdin.read())
    print(data.get("tool_input", {}).get("command", ""))
except Exception:
    print("")
PYEOF
) || { echo "$INPUT"; exit 0; }

if [[ -z "$CMD" ]]; then
    echo "$INPUT"
    exit 0
fi

MANIFEST=".claude/locked-files.txt"
[[ -f "$MANIFEST" ]] || { echo "$INPUT"; exit 0; }

UNLOCK="${CLAUDE_UNLOCK:-}"

# Extract candidate target paths from the command string.
# Heuristics — broad matches; we err on the side of catching too much, then check manifest.
targets=$(printf '%s\n' "$CMD" | python3 - <<'PYEOF'
import re, sys

cmd = sys.stdin.read()
patterns = [
    r'>\s*([^\s|;&<>]+)',                       # redirect: > FILE or >> FILE
    r'\btee\s+(?:-a\s+)?([^\s|;&]+)',           # tee FILE / tee -a FILE
    r'\bsed\s+(?:[^|;&]*\s)?-i[^\s]*\s+(?:[^\s|;&]+\s+)*([^\s|;&]+)',
    r'\bperl\s+(?:[^|;&]*\s)?-i[^\s]*\s+(?:[^\s|;&]+\s+)*([^\s|;&]+)',
    r'\b(?:cp|mv)\s+(?:-[^\s]+\s+)*[^\s|;&]+\s+([^\s|;&]+)',
]
hits = set()
for p in patterns:
    for m in re.finditer(p, cmd):
        target = m.group(1).strip("\"'")
        if target and not target.startswith('-'):
            hits.add(target)
print('\n'.join(hits))
PYEOF
)

[[ -z "$targets" ]] && { echo "$INPUT"; exit 0; }

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

match_glob() {
    local pattern="$1" path="$2"
    case "$path" in
        $pattern) return 0 ;;
        *) return 1 ;;
    esac
}

while IFS= read -r raw_target; do
    [[ -z "$raw_target" ]] && continue
    # Strip leading repo root if absolute.
    target="${raw_target#$REPO_ROOT/}"
    target="${target#./}"

    while IFS= read -r line; do
        [[ -z "$line" || "$line" =~ ^# ]] && continue
        tier="soft"; pattern="$line"
        if [[ "$line" == !* ]]; then tier="hard"; pattern="${line#!}"; fi

        if match_glob "$pattern" "$target"; then
            if [[ -n "$UNLOCK" ]] && match_glob "$UNLOCK" "$target"; then
                continue 2  # bypass — try next target
            fi
            if [[ "$tier" == "hard" ]]; then
                echo "┌─ Bash locked-file BLOCK" >&2
                echo "│  Command attempts to write: $target" >&2
                echo "│  Matched Tier 1 entry: $line" >&2
                echo "│  Set CLAUDE_UNLOCK='$pattern' to override." >&2
                echo "└─ ✗ Command blocked" >&2
                exit 2
            else
                echo "┌─ Bash locked-file WARN" >&2
                echo "│  Command writes to Tier 2 path: $target" >&2
                echo "│  Matched: $line" >&2
                echo "└─ ⚠ Proceeding with warning" >&2
            fi
        fi
    done < "$MANIFEST"
done <<<"$targets"

echo "$INPUT"
exit 0
```

```bash
chmod +x .claude/hooks/pre-bash-locked-files.sh
```

### 2.3 Smoke test

```bash
# Tier 1 redirect → block
echo '{"tool_input": {"command": "echo x > LICENSE"}}' \
  | bash .claude/hooks/pre-bash-locked-files.sh
echo "exit=$?"   # expect 2

# Innocent command → pass
echo '{"tool_input": {"command": "ls -la"}}' \
  | bash .claude/hooks/pre-bash-locked-files.sh
echo "exit=$?"   # expect 0

# sed -i on workflow → block
echo '{"tool_input": {"command": "sed -i s/foo/bar/ .github/workflows/lint.yml"}}' \
  | bash .claude/hooks/pre-bash-locked-files.sh
echo "exit=$?"   # expect 2
```

If a smoke test fails (especially on macOS where BSD sed differs), inspect the regex
output and adjust. Do NOT loosen the patterns to make tests pass — instead add the
specific failing case to the regex set.

---

## Phase 3 — Register both hooks in `settings.json`

`.claude/settings.json` is itself Tier 1 — the very first edit will trigger your hook
before it is even registered. Use the bypass:

```bash
export CLAUDE_UNLOCK='.claude/settings.json'
```

(After this phase commits, unset it: `unset CLAUDE_UNLOCK`.)

### 3.1 Add hook entries

Open `.claude/settings.json`. Find the `"PreToolUse"` array. Insert these entries at the
TOP of the array (before any existing PreToolUse hook), so locked-file checks run first
and can short-circuit:

```json
{
  "matcher": "Write|Edit|MultiEdit",
  "hooks": [
    {
      "type": "command",
      "command": "bash .claude/hooks/pre-write-locked-files.sh"
    }
  ],
  "description": "Block edits to files listed in .claude/locked-files.txt (Tier 1) and warn on Tier 2"
},
{
  "matcher": "Bash",
  "hooks": [
    {
      "type": "command",
      "command": "bash .claude/hooks/pre-bash-locked-files.sh"
    }
  ],
  "description": "Block shell commands writing to locked paths (redirects, tee, sed -i, etc.)"
},
```

### 3.2 Add `permissions.deny` entries

Append to the existing `"permissions"."deny"` array. Generate the list by reading the
manifest and emitting `Edit(<glob>)`, `Write(<glob>)`, `MultiEdit(<glob>)` for every
Tier-1 entry:

```bash
grep '^!' .claude/locked-files.txt | sed 's/^!//' | while read -r p; do
  printf '      "Edit(%s)",\n      "Write(%s)",\n      "MultiEdit(%s)",\n' "$p" "$p" "$p"
done
```

Paste the output into the `deny` array. Result for `LICENSE` should look like:

```json
"deny": [
  "Bash(git push:*)",
  "Bash(uv publish:*)",
  "Bash(git commit --no-verify:*)",
  "Bash(git push --force:*)",
  "Edit(LICENSE)",
  "Write(LICENSE)",
  "MultiEdit(LICENSE)",
  "Edit(template/LICENSE.jinja)",
  "...etc..."
]
```

JSON validity: run `python3 -m json.tool .claude/settings.json > /dev/null` — must exit 0.

### 3.3 Mirror to `template/.claude/settings.json`

Generated projects also need protection. Repeat 3.1 and 3.2 for
`template/.claude/settings.json`, but use a TRIMMED manifest list — generated projects
do not have `template/`, `copier.yml`, or meta-only paths. Use only:

- `LICENSE`
- `pyproject.toml` (Tier 2)
- `uv.lock`
- `.secrets.baseline`
- `.gitignore`
- `.pre-commit-config.yaml`
- `.github/workflows/**`
- `.github/dependabot.yml`
- `.claude/settings.json`
- `.claude/locked-files.txt` (the file itself will be created in template too — see Phase 5)
- `.claude/hooks/pre-write-locked-files.sh`
- `.claude/hooks/pre-bash-locked-files.sh`

### 3.4 Validation

```bash
python3 -m json.tool .claude/settings.json > /dev/null && echo "settings.json OK"
python3 -m json.tool template/.claude/settings.json > /dev/null && echo "template OK"
unset CLAUDE_UNLOCK
```

Commit (with bypass active for the settings file you just wrote):

```bash
CLAUDE_UNLOCK='.claude/settings.json' git add .claude/settings.json template/.claude/settings.json
git add .claude/locked-files.txt .claude/hooks/pre-write-locked-files.sh .claude/hooks/pre-bash-locked-files.sh
git commit -m "feat(claude): add file-locking via manifest, hooks, and permissions.deny"
```

---

## Phase 4 — `just lock-sync` recipe

Hand-syncing `permissions.deny` against the manifest will drift. Add a justfile recipe.

### 4.1 Edit `justfile`

`justfile` is Tier 2 — you will get a warning, not a block. Append at the end:

```makefile
# -------------------------------------------------------------------------
# File-locking
# -------------------------------------------------------------------------

# Sync .claude/settings.json permissions.deny with .claude/locked-files.txt (Tier 1 only).
# Print-only by default; use `just lock-sync APPLY=1` to write.
lock-sync APPLY="0":
    @uv run python scripts/sync_lock_manifest.py {{ if APPLY == "1" { "--apply" } else { "" } }}

# List all locked files (Tier 1 + Tier 2) from the manifest.
lock-list:
    @grep -v '^#\|^$$' .claude/locked-files.txt | sed 's/^!/[T1] /; t; s/^/[T2] /'
```

### 4.2 Create `scripts/sync_lock_manifest.py`

This script reads the manifest, computes the desired `permissions.deny` Tier-1 entries,
diffs against the actual JSON, prints the diff, and optionally writes.

Skeleton (the executor must complete docstrings/types per project style):

```python
"""Sync .claude/settings.json permissions.deny against .claude/locked-files.txt.

Reads the manifest, computes the desired set of Edit(<path>), Write(<path>),
MultiEdit(<path>) entries for every Tier 1 (`!`-prefixed) line, compares against
the current settings.json deny list, and prints the diff. With --apply, writes
the merged result back to settings.json (preserving non-locking deny entries
such as Bash(git push:*)).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / ".claude" / "locked-files.txt"
SETTINGS = REPO_ROOT / ".claude" / "settings.json"


def read_tier1_paths(manifest: Path) -> list[str]:
    """Return the list of Tier-1 (hard-lock) paths from the manifest."""
    out: list[str] = []
    for raw in manifest.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("!"):
            out.append(line[1:])
    return out


def desired_deny_entries(paths: list[str]) -> list[str]:
    """Build the deny strings for each Tier-1 path."""
    entries: list[str] = []
    for p in paths:
        entries.append(f"Edit({p})")
        entries.append(f"Write({p})")
        entries.append(f"MultiEdit({p})")
    return entries


def main() -> int:
    """Entry point — diff or apply the lock manifest sync."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write changes to settings.json")
    args = parser.parse_args()

    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    deny = settings.setdefault("permissions", {}).setdefault("deny", [])

    desired = desired_deny_entries(read_tier1_paths(MANIFEST))
    desired_set = set(desired)
    existing_lock_entries = {
        e for e in deny if e.startswith(("Edit(", "Write(", "MultiEdit("))
    }
    non_lock = [e for e in deny if not e.startswith(("Edit(", "Write(", "MultiEdit("))]

    to_add = sorted(desired_set - existing_lock_entries)
    to_remove = sorted(existing_lock_entries - desired_set)

    print(f"Manifest Tier-1 paths: {len(desired) // 3}")
    print(f"Entries to add:    {len(to_add)}")
    print(f"Entries to remove: {len(to_remove)}")
    for e in to_add:
        print(f"  + {e}")
    for e in to_remove:
        print(f"  - {e}")

    if not args.apply:
        if to_add or to_remove:
            print("\nRun with --apply (or `just lock-sync APPLY=1`) to write.")
            return 1
        print("settings.json already in sync with manifest.")
        return 0

    new_deny = sorted(set(non_lock) | desired_set, key=lambda s: (not s.startswith("Bash"), s))
    settings["permissions"]["deny"] = new_deny
    SETTINGS.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print("Wrote .claude/settings.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 4.3 Add a corresponding test

`tests/test_sync_lock_manifest.py` (per the strict-TDD convention — write the test first
in real practice; here you are retrofitting). Cover:

- Manifest with no Tier-1 entries → no deny additions.
- Manifest with one Tier-1 entry → three deny additions (Edit/Write/MultiEdit).
- Existing non-lock deny entries (e.g. `Bash(git push:*)`) are preserved.
- `--apply` writes valid JSON; without `--apply` does not modify the file.

### 4.4 Validation

```bash
just lock-list                # prints all locked entries with [T1]/[T2] prefix
just lock-sync                # diff only — should print "already in sync" after Phase 3
just test                     # all tests pass
```

Commit:

```bash
git add justfile scripts/sync_lock_manifest.py tests/test_sync_lock_manifest.py
git commit -m "feat(lock): add just lock-sync and lock-list recipes"
```

---

## Phase 5 — Mirror to template/

Generated projects need their own copies of the hooks and a starter manifest. Mirror:

```bash
cp .claude/hooks/pre-write-locked-files.sh template/.claude/hooks/
cp .claude/hooks/pre-bash-locked-files.sh template/.claude/hooks/
chmod +x template/.claude/hooks/pre-write-locked-files.sh
chmod +x template/.claude/hooks/pre-bash-locked-files.sh
```

Create `template/.claude/locked-files.txt` with the trimmed list from Phase 3.3:

```text
# Locked-file manifest for generated projects.
# See template/.claude/CLAUDE.md (or the Cookiecutter README) for usage.

!LICENSE
!uv.lock
!.secrets.baseline
!.gitignore
!.pre-commit-config.yaml
!.github/workflows/**
!.github/dependabot.yml
!.claude/settings.json
!.claude/locked-files.txt
!.claude/hooks/pre-write-locked-files.sh
!.claude/hooks/pre-bash-locked-files.sh

pyproject.toml
justfile
.claude/rules/**/*.md
.claude/commands/**/*.md
```

The hook entries you added to `template/.claude/settings.json` in Phase 3.3 already
reference these scripts, so this completes the wiring.

### 5.1 Update template tests

Edit `tests/test_template.py` to assert that a fresh `copier copy` produces:

- `.claude/locked-files.txt` (file exists, contains `!LICENSE`)
- `.claude/hooks/pre-write-locked-files.sh` (executable bit set)
- `.claude/hooks/pre-bash-locked-files.sh` (executable bit set)
- `.claude/settings.json` `permissions.deny` includes `Edit(LICENSE)`

### 5.2 Validation

```bash
just sync-check     # root↔template parity must still pass
just test           # template tests must pass
```

Commit:

```bash
git add template/.claude/ tests/test_template.py
git commit -m "feat(template): mirror file-locking into generated projects"
```

---

## Phase 6 — CLAUDE.md documentation

Hooks and `permissions.deny` are enforcement; documentation is so the model never tries.
Add a "Locked files" section to root `CLAUDE.md` and `template/CLAUDE.md.jinja`.

### 6.1 Root `CLAUDE.md`

CLAUDE.md is NOT in the Tier-2 list (intentional — it evolves). Add this section after
"Files you should never modify directly":

```markdown
## File locking (Claude Code)

This repository uses a manifest-driven file-locking system to prevent agents from
modifying stable files without explicit user intent.

- **Manifest:** `.claude/locked-files.txt` — single source of truth.
- **Tier 1 (hard lock, prefix `!`):** blocked by both a PreToolUse hook AND
  `permissions.deny`. Editing requires the user to set `CLAUDE_UNLOCK=<path>` in the
  environment AND (for `permissions.deny` overrides) edit `settings.json` directly.
- **Tier 2 (soft lock, no prefix):** hook prints a warning but allows the edit. Used for
  files that evolve but should not be reformatted casually.
- **Tier 3 (everything else):** no restriction.

Agents must consult `.claude/locked-files.txt` BEFORE attempting to edit anything in
`.github/workflows/`, `LICENSE`, `pyproject.toml`, `copier.yml`, `justfile`, or any other
infrastructure file. If a change is genuinely needed, ask the user to confirm and to set
`CLAUDE_UNLOCK`.

Sync `permissions.deny` against the manifest with:

    just lock-sync           # diff only
    just lock-sync APPLY=1   # write
```

### 6.2 `template/CLAUDE.md.jinja`

Mirror the same section, but reference the trimmed manifest. Do not include the Copier-
specific paths (`copier.yml`, `template/`).

### 6.3 Update `.claude/CLAUDE.md` orientation

Add a one-paragraph mention of the locked-files manifest in `.claude/CLAUDE.md`'s
"Directory layout" or "settings.json" section pointing at `.claude/locked-files.txt`.

### 6.4 Validation

```bash
grep -q "locked-files.txt" CLAUDE.md && echo OK
grep -q "locked-files.txt" template/CLAUDE.md.jinja && echo OK
grep -q "locked-files.txt" .claude/CLAUDE.md && echo OK
just docs-check
```

Commit:

```bash
git add CLAUDE.md template/CLAUDE.md.jinja .claude/CLAUDE.md
git commit -m "docs: document file-locking system in CLAUDE.md (root + template)"
```

---

## Phase 7 — End-to-end verification

### 7.1 Live test of the full stack

With NO `CLAUDE_UNLOCK` set, attempt these in your Claude Code session and confirm each
fails as expected:

| Action | Expected outcome |
|---|---|
| Edit `LICENSE` | `permissions.deny` blocks before the hook runs |
| Edit `.github/workflows/tests.yml` | `permissions.deny` blocks |
| Edit `pyproject.toml` (Tier 2) | hook prints WARN; edit proceeds |
| `cat > LICENSE` via Bash | `pre-bash-locked-files.sh` blocks |
| Edit `docs/notes.md` | no restriction |

With `CLAUDE_UNLOCK='LICENSE'` set:

| Action | Expected outcome |
|---|---|
| Edit `LICENSE` via Edit tool | `permissions.deny` STILL blocks (env var does not override deny) |
| `cat > LICENSE` via Bash | hook bypasses; command runs |

This second behaviour is intentional. `permissions.deny` is the strongest layer because
it requires an interactive UI confirmation; `CLAUDE_UNLOCK` is the relief valve for
hook-only enforcement. To edit a Tier-1 file via the Edit tool, the user must edit
`settings.json` to remove the deny entry — which itself requires `CLAUDE_UNLOCK` set on
`.claude/settings.json`. This is the meta-lock by design.

### 7.2 Full CI

```bash
just ci
```

Must pass.

### 7.3 PR

```bash
git push -u origin chore/file-locking-claude-code
```

PR body template:

```
## Summary

Implements manifest-driven file locking for Claude Code agents.

## What changed

- New manifest: `.claude/locked-files.txt` (Tier 1 / Tier 2 entries)
- New hooks: `pre-write-locked-files.sh`, `pre-bash-locked-files.sh`
- `permissions.deny` synced from manifest (Tier 1 only)
- New justfile recipes: `just lock-sync`, `just lock-list`
- New script: `scripts/sync_lock_manifest.py` (+ tests)
- Mirrored into `template/.claude/` for generated projects
- Documented in CLAUDE.md (root + template)

## How agents bypass when a change is needed

- Tier 2 (soft): set `CLAUDE_UNLOCK=<path>` for the session.
- Tier 1 (hard): user removes the entry from `.claude/locked-files.txt` AND/OR
  `.claude/settings.json` deny list. Editing those files itself requires `CLAUDE_UNLOCK`.

## Validation

- `just ci` passes
- 5 hook smoke tests in Phase 1.2 / 2.3 all behave as expected
- Live test matrix in Phase 7.1 matches expected outcomes
```

---

## Anti-goals — what NOT to do

- **Do NOT** add Tier-1 entries for files the project actively edits (e.g. `README.md`,
  `CLAUDE.md`, anything under `docs/`, any `tests/` or `scripts/` file). This will quickly
  make the repo unworkable.
- **Do NOT** rely on `CLAUDE.md` guidance alone. It is the weakest layer; always pair
  with the hook and (for true Tier 1) `permissions.deny`.
- **Do NOT** create per-file hooks. One generic hook reading the manifest is the point.
- **Do NOT** skip the meta-lock entries (`.claude/settings.json`, the manifest itself,
  the lock hooks). Without these, an agent can simply edit the manifest to remove its
  own restrictions.
- **Do NOT** add file-locking to git pre-commit hooks. This document is scoped to Claude
  Code only — git-level enforcement is a separate problem.
- **Do NOT** widen the Bash-redirect regex to catch every conceivable shell trick.
  Determined adversarial bypass is out of scope; the goal is to prevent accidental
  modification, not to be a security boundary.
- **Do NOT** modify `uv.lock`, `.copier-answers.yml`, or any `.jinja` template body
  while implementing this plan beyond what is explicitly listed.

---

## Quick reference — final expected state

| Artefact | Location |
|---|---|
| Manifest | `.claude/locked-files.txt` |
| Write/Edit hook | `.claude/hooks/pre-write-locked-files.sh` |
| Bash hook | `.claude/hooks/pre-bash-locked-files.sh` |
| Hook registrations | `.claude/settings.json` PreToolUse |
| Hard-lock denies | `.claude/settings.json` permissions.deny |
| Sync script | `scripts/sync_lock_manifest.py` |
| Sync recipe | `just lock-sync` (+ `just lock-list`) |
| Sync tests | `tests/test_sync_lock_manifest.py` |
| Template manifest | `template/.claude/locked-files.txt` |
| Template hooks | `template/.claude/hooks/pre-{write,bash}-locked-files.sh` |
| Documentation | `CLAUDE.md`, `template/CLAUDE.md.jinja`, `.claude/CLAUDE.md` |

Bypass mechanisms:

| Layer | Bypass |
|---|---|
| `permissions.deny` (Tier 1) | User edits `.claude/settings.json` (which itself requires bypass) |
| Hooks (Tier 1 + Tier 2) | `CLAUDE_UNLOCK=<path-or-glob>` env var |
| `CLAUDE.md` guidance | None — soft layer, model-side only |

If any row in this section is not satisfied at the end of execution, the plan is not
complete.

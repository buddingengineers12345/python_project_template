---
name: bash-guide
description: >-
  Expert bash scripting skill for writing, maintaining, and updating
  production-quality shell scripts. Use this skill whenever the user asks to
  write a bash script, create a shell utility, automate a task with shell,
  update or refactor an existing .sh file, add logging to a script, handle
  errors in bash, set up script structure, or follow shell best practices.
  Also triggers for: "write me a script", "shell automation", "bash function",
  "cron job script", "deployment script", "wrapper script", or any task
  producing a .sh or executable shell file. Covers Google Shell Style Guide
  compliance, dual-mode logging (human vs LLM execution contexts), and
  LLM-agent readability patterns.
---

# Bash Guide Skill

Produce bash scripts that are correct (safe defaults, proper quoting, reliable
error handling), readable by humans (clear structure, comments, named variables),
readable by LLM agents (structured output, machine-parseable logs, deterministic
exit codes), and maintainable (modular, documented, easy to update).

Authority: [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html).

## When to use bash (and when not to)

Use bash when calling other utilities with minimal data transformation, writing
small glue scripts (under ~150 lines), or automating sequential shell operations.

Switch to Python/Go/etc. when the script exceeds ~150 lines or has complex
control flow, heavy data manipulation is required, performance matters, or data
structures beyond arrays are needed.

## Workflow

### 1. Determine execution context

Before writing, check (or ask) for these environment variables, which drive how
logging behaves:

```
EXECUTION_CONTEXT   "llm" | "human"                  (default: "human")
HUMAN_LOG_LEVEL     "debug"|"info"|"warn"|"error"    (default: "info")
LLM_LOG_LEVEL       "debug"|"info"|"warn"|"error"    (default: "info")
```

### 2. Start from the skeleton

For any new script, copy [templates/script-skeleton.sh](templates/script-skeleton.sh).
It includes `set -euo pipefail`, standard constants, a minimal dual-mode logging
library, `usage()`, `die()`, exit-code constants, and an arg-parsing `main()`.

Every script follows this top-to-bottom layout:

1. Shebang + `set -euo pipefail`
2. File header comment (name, description, usage, version)
3. Global constants (`readonly`)
4. Sourced libraries (if any)
5. Logging functions (or source shared lib)
6. Helper / utility functions
7. Core logic functions
8. `main()` function
9. `main "$@"` as the last non-comment line

For the rationale, header format, and function-comment convention, see
[references/structure.md](references/structure.md).

### 3. Pick the right logging mode

**`EXECUTION_CONTEXT=human` (default)** — colorized, human-friendly messages to
STDERR with ISO-8601 timestamps:

```
[2026-04-15T10:23:01Z] [INFO ] Starting deploy.sh v2.1.0
[2026-04-15T10:23:02Z] [WARN ] Config file not found — using defaults
```

**`EXECUTION_CONTEXT=llm`** — structured key=value lines to STDERR. No color
codes (they corrupt LLM parsing). One event per line. Machine-parseable:

```
[2026-04-15T10:23:01Z] LEVEL=INFO SCRIPT=deploy.sh MSG="Starting deploy.sh v2.1.0"
[2026-04-15T10:23:02Z] LEVEL=WARN SCRIPT=deploy.sh MSG="Config file not found"
```

Rules for LLM mode (critical — violations break downstream agents):

- No ANSI escape codes
- All log output to STDERR; script data/payload output to STDOUT only
- Short, unambiguous `KEY=VALUE` fields
- No multi-line log messages
- Exit codes documented and deterministic

For the full logging library (rotation, JSON mode, structured fields), see
[references/logging.md](references/logging.md).

### 4. Follow Google naming & formatting

| Element         | Convention              | Example                        |
|-----------------|-------------------------|--------------------------------|
| Functions       | `snake_case`            | `deploy_artifact()`            |
| Local variables | `snake_case`            | `local file_path`              |
| Constants / env | `UPPER_SNAKE_CASE`      | `readonly MAX_RETRIES=3`       |
| Source files    | `lowercase_with_unders` | `deploy_helpers.sh`            |
| Indentation     | 2 spaces, no tabs       | —                              |
| Line length     | ≤ 80 chars              | (URLs/paths exempt)            |
| Variable expand | `"${var}"` always       | `"${array[@]}"` for arrays     |
| Numeric compare | `(( ))`                 | `(( count > threshold ))`      |

Control-flow layout: `; then` and `; do` on the same line as `if`/`for`/`while`.

### 5. Handle errors deterministically

`set -euo pipefail` goes at the top of every script:

- `-e` — exit on unhandled non-zero return
- `-u` — error on unset variable references
- `-o pipefail` — a pipeline fails if any segment fails

Prefer inline checks for critical operations:

```bash
if ! cp "${src}" "${dst}"; then
  die "Failed to copy ${src} to ${dst}"
fi
```

For pipelines, consult `PIPESTATUS`:

```bash
tar -cf - ./* | gzip > archive.tar.gz
pipe_status=("${PIPESTATUS[@]}")
if (( pipe_status[0] != 0 || pipe_status[1] != 0 )); then
  die "Archive failed (tar=${pipe_status[0]}, gzip=${pipe_status[1]})"
fi
```

Document exit codes as constants (`EXIT_OK`, `EXIT_USAGE`, `EXIT_IO`, …) so LLM
callers can branch on them. For LLM-executable scripts, emit a final structured
line containing `EXIT_CODE=<n> REASON="..."` before `exit`.

For arg-parsing patterns (`getopts` vs. manual), `trap` cleanup, array idioms,
heredocs, and retry loops, see [references/patterns.md](references/patterns.md).

### 6. LLM-agent readability checklist

When a script will be invoked or parsed by an LLM agent, verify:

- [ ] `EXECUTION_CONTEXT=llm` is supported and tested
- [ ] All log output goes to STDERR; payload data goes to STDOUT
- [ ] Log lines are single-line, key=value structured in llm mode
- [ ] Exit codes are documented and consistent
- [ ] `--help` / `-h` outputs a clean block an agent can parse
- [ ] Functions have header comments (Globals / Arguments / Outputs / Returns)
- [ ] No interactive prompts (`read -p`) when `EXECUTION_CONTEXT=llm`
- [ ] Script signals completion clearly (final log line or structured `EXIT_CODE`)

## Maintaining existing scripts

When asked to modify an existing script:

1. **Read fully first** — understand existing style, logging approach, and
   variable names before editing.
2. **Preserve style** — if the script uses 4-space indent, keep it. Don't
   impose new style on partial edits.
3. **Locate insertion points** — add functions near existing ones of the same
   type; never insert executable code between function definitions.
4. **Update the version string** if present in the header.
5. **Mark incomplete work** with `# TODO(agent): <reason>`.
6. **Mentally trace** the modified path with a sample input.

For larger refactors, propose a plan (what will change, what stays, new deps or
env vars introduced) before executing.

## Quick patterns cheat-sheet

```bash
# Safe temp dir with cleanup
readonly TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

# Read file into array safely (bash 4+)
readarray -t lines < <(grep "pattern" "${file}")

# Check required env vars
for var in REQUIRED_VAR_1 REQUIRED_VAR_2; do
  [[ -z "${!var:-}" ]] && die "Required env var not set: ${var}"
done

# Retry loop
attempt=0
until command_to_try || (( ++attempt >= MAX_RETRIES )); do
  log_warn "Attempt ${attempt} failed, retrying..."
  sleep $(( attempt * 2 ))
done
(( attempt >= MAX_RETRIES )) && die "Failed after ${MAX_RETRIES} attempts"
```

For the full pattern library, see [references/patterns.md](references/patterns.md).

## When to load references

| If the task involves…                      | Load                            |
|---------------------------------------------|---------------------------------|
| Script headers, `main()` layout, comments  | `references/structure.md`       |
| Dual-mode logging, JSON log output         | `references/logging.md`         |
| Arg parsing, traps, arrays, retries        | `references/patterns.md`        |
| Starting a new script from scratch         | `templates/script-skeleton.sh`  |
| Simple script edit or small function       | No reference needed — use inline |

## Efficiency: batch edits and parallel calls

- **Batch edits:** When adding multiple functions to a script, write them all in
  a single Edit call rather than one function at a time.
- **Read before edit:** Read the full script first to understand its structure,
  existing style, and variable names before making any changes.

## Quick reference: where to go deeper

| Topic                                                | Reference file                                                 |
|------------------------------------------------------|----------------------------------------------------------------|
| Script skeleton, headers, `main()` convention        | [references/structure.md](references/structure.md)             |
| Full dual-context logging library                    | [references/logging.md](references/logging.md)                 |
| Arg parsing, traps, arrays, retries, heredocs        | [references/patterns.md](references/patterns.md)               |
| Copy-paste starter script                            | [templates/script-skeleton.sh](templates/script-skeleton.sh)   |

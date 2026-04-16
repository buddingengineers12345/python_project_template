# Script structure reference

## Complete File Header Format

```bash
#!/bin/bash
#
# SCRIPT NAME: <script_name>.sh
# DESCRIPTION: <One-sentence description of what this script does>
# USAGE:       ./<script_name>.sh [OPTIONS] <REQUIRED_ARG>
#
# OPTIONS:
#   -h, --help       Show this help and exit
#   -v, --verbose    Enable debug-level logging
#   -n, --dry-run    Simulate actions without making changes
#
# ENVIRONMENT VARIABLES:
#   EXECUTION_CONTEXT   llm|human   Controls log format (default: human)
#   HUMAN_LOG_LEVEL     debug|info|warn|error  (default: info)
#   LLM_LOG_LEVEL       debug|info|warn|error  (default: info)
#
# EXIT CODES:
#   0   Success
#   1   Usage / argument error
#   2   Missing dependency
#   3   I/O error (file not found, permission denied)
#   4   Runtime error
#
# EXAMPLES:
#   ./<script_name>.sh --help
#   EXECUTION_CONTEXT=llm ./<script_name>.sh process input.txt
#
# AUTHOR:      <name or "agent">
# VERSION:     1.0.0
# UPDATED:     YYYY-MM-DD
```

---

## Function Comment Format (required for all non-trivial functions)

```bash
#######################################
# Brief description of what this does.
# Globals:
#   VARIABLE_READ   (reads but doesn't modify)
#   VARIABLE_WRITE  (modifies)
# Arguments:
#   $1 - Description of first argument
#   $2 - Description of second argument (optional)
# Outputs:
#   Writes result to STDOUT
#   Writes errors/warnings to STDERR via log_*
# Returns:
#   0 on success
#   1 if <condition>
#   3 if file not found
#######################################
my_function() {
  local arg1="$1"
  local arg2="${2:-default_value}"
  ...
}
```

---

## Canonical File Layout (annotated)

```
Line 1      : #!/bin/bash
Lines 2-N   : File header comment block
             
N+1         : set -euo pipefail
N+2         : (blank line)

SECTION 1 — Constants
  All readonly globals
  EXECUTION_CONTEXT, HUMAN_LOG_LEVEL, LLM_LOG_LEVEL
  Exit code constants

SECTION 2 — Sourced libraries
  source "${SCRIPT_DIR}/lib/logging.sh"   (if external)
  source "${SCRIPT_DIR}/lib/utils.sh"

SECTION 3 — Logging functions
  _log_level_value()
  log()
  log_debug() log_info() log_warn() log_error()

SECTION 4 — Utility / helper functions
  usage()
  die()
  cleanup_and_exit()
  check_dependencies()

SECTION 5 — Core logic functions
  (named clearly, one responsibility each)

SECTION 6 — main()
  Argument parsing (while/case)
  Dependency checks
  Core function calls
  Exit

Last line   : main "$@"
```

---

## Argument Parsing with getopts (POSIX-style)

Use for simple short options:

```bash
parse_args() {
  local OPTIND opt
  while getopts ":hvn" opt; do
    case "${opt}" in
      h) usage; exit 0 ;;
      v) export HUMAN_LOG_LEVEL="debug"; export LLM_LOG_LEVEL="debug" ;;
      n) readonly DRY_RUN=true ;;
      :) die "Option -${OPTARG} requires an argument" ;;
      \?) die "Unknown option: -${OPTARG}" ;;
    esac
  done
  shift $(( OPTIND - 1 ))
  # Remaining positional args are in "$@"
}
```

For long options, use a while/case loop (see patterns.md).

---

## Dependency Checking

```bash
#######################################
# Verify required commands exist on PATH.
# Arguments:
#   One or more command names
# Returns:
#   0 if all present; exits with code 2 if any missing
#######################################
check_dependencies() {
  local -a missing=()
  for cmd in "$@"; do
    if ! command -v "${cmd}" &>/dev/null; then
      missing+=("${cmd}")
    fi
  done
  if (( ${#missing[@]} > 0 )); then
    log_error "Missing required commands: ${missing[*]}"
    exit 2
  fi
  log_debug "Dependencies satisfied: $*"
}

# Usage in main():
check_dependencies curl jq git docker
```

---

## Trap / Cleanup Pattern

```bash
# Declare cleanup function before setting trap
cleanup() {
  local exit_code=$?
  log_debug "Cleaning up (exit_code=${exit_code})"
  # Remove temp files, release locks, etc.
  rm -rf "${TMP_DIR:-}"
  # Always exit with the original code
  exit "${exit_code}"
}

trap cleanup EXIT
trap 'log_error "Interrupted"; exit 130' INT TERM
```

---

## Modular / Library Scripts

Library scripts (sourced, not executed):
- Extension: `.sh`
- Not executable (`chmod -x`)
- Begin with a guard:

```bash
#!/bin/bash
# lib/utils.sh — utility functions for <project>
# Source this file; do not execute directly.

# Guard against direct execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo "This file must be sourced, not executed." >&2
  exit 1
fi
```
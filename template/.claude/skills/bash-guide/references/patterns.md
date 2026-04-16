# Bash patterns reference

## Long-option Argument Parsing

```bash
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
        usage
        exit 0
        ;;
      -v|--verbose)
        export HUMAN_LOG_LEVEL="debug"
        export LLM_LOG_LEVEL="debug"
        shift
        ;;
      -n|--dry-run)
        readonly DRY_RUN=true
        shift
        ;;
      --output=*)
        readonly OUTPUT_FILE="${1#--output=}"
        shift
        ;;
      --output)
        readonly OUTPUT_FILE="$2"
        shift 2
        ;;
      --)
        shift
        break
        ;;
      -*)
        die 1 "Unknown option: $1"
        ;;
      *)
        # First positional arg
        readonly INPUT_FILE="$1"
        shift
        ;;
    esac
  done

  # Validate required arguments
  [[ -z "${INPUT_FILE:-}" ]] && die 1 "INPUT_FILE is required. See --help."
}
```

---

## Safe Array Patterns

```bash
# Declare explicitly
declare -a items=()

# Append
items+=("new item with spaces")
items+=("another item")

# Iterate safely (never unquoted)
for item in "${items[@]}"; do
  process "${item}"
done

# Pass to a command
run_cmd "${items[@]}"

# Length
echo "Count: ${#items[@]}"

# Slice
subset=("${items[@]:1:3}")    # items[1], items[2], items[3]

# Read file into array (bash 4+)
readarray -t lines < <(cat "${file}")

# Join array into string
joined="$(IFS=','; echo "${items[*]}")"
```

---

## Robust File / Path Handling

```bash
# Always quote paths
cp "${src_file}" "${dst_dir}/"

# Check existence before use
[[ -f "${file}" ]]  || die 3 "File not found: ${file}"
[[ -d "${dir}" ]]   || die 3 "Directory not found: ${dir}"
[[ -r "${file}" ]]  || die 3 "Cannot read: ${file}"
[[ -w "${dir}" ]]   || die 3 "Cannot write to: ${dir}"

# Wildcard expansion — use explicit paths to avoid -flag filenames
for f in ./*; do
  process_file "${f}"
done

# Temp directory with guaranteed cleanup
readonly TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

# Resolve canonical path
real_path="$(realpath "${input_path}")"
```

---

## Heredoc Patterns

```bash
# Basic heredoc
cat <<'EOF'
This text won't expand $VARIABLES.
EOF

# Variable-expanding heredoc
cat <<EOF
Hostname: $(hostname)
User: ${USER}
EOF

# Heredoc into a variable
read -r -d '' config_content <<'EOF' || true
key1=value1
key2=value2
EOF

# Tab-indented heredoc (use real tabs)
if true; then
	cat <<-EOF
		This is indented with tabs.
		Tabs are stripped by <<-.
	EOF
fi
```

---

## Retry with Backoff

```bash
#######################################
# Retry a command with exponential backoff.
# Globals:
#   None
# Arguments:
#   $1 - Max attempts (integer)
#   $@ - Command and its arguments
# Returns:
#   Exit code of the command, or 1 if all attempts fail
#######################################
retry() {
  local max_attempts="$1"; shift
  local attempt=1
  local wait_seconds=1

  until "$@"; do
    if (( attempt >= max_attempts )); then
      log_error "Command failed after ${max_attempts} attempts: $*"
      return 1
    fi
    log_warn "Attempt ${attempt}/${max_attempts} failed. Retrying in ${wait_seconds}s..."
    sleep "${wait_seconds}"
    (( attempt++ ))
    (( wait_seconds = wait_seconds * 2 ))
  done
  log_debug "Command succeeded on attempt ${attempt}: $*"
}

# Usage:
retry 5 curl -sf "https://example.com/api"
```

---

## String Manipulation (prefer builtins over sed/awk)

```bash
# Trim prefix
path="${full_path#/tmp/}"

# Trim suffix
name="${filename%.sh}"

# Replace first match
new="${string/old/new}"

# Replace all matches
new="${string//old/new}"

# Uppercase / lowercase (bash 4+)
upper="${var^^}"
lower="${var,,}"

# Substring: ${var:start:length}
first4="${var:0:4}"

# Length
len="${#var}"

# Default value if unset or empty
val="${MY_VAR:-default}"

# Error if unset
val="${REQUIRED_VAR:?'REQUIRED_VAR must be set'}"

# Regex match (use BASH_REMATCH)
if [[ "${input}" =~ ^([0-9]{4})-([0-9]{2})-([0-9]{2})$ ]]; then
  year="${BASH_REMATCH[1]}"
  month="${BASH_REMATCH[2]}"
  day="${BASH_REMATCH[3]}"
fi
```

---

## Process Substitution vs Pipes

```bash
# WRONG: pipe creates subshell; $last_line stays 'NULL' outside
last_line='NULL'
your_cmd | while read -r line; do
  last_line="${line}"
done
echo "${last_line}"   # prints NULL

# RIGHT: process substitution keeps vars in current shell
last_line='NULL'
while read -r line; do
  last_line="${line}"
done < <(your_cmd)
echo "${last_line}"   # prints last non-empty line

# ALSO RIGHT: readarray (bash 4+)
readarray -t lines < <(your_cmd)
last_line="${lines[-1]}"
```

---

## Numeric Arithmetic

```bash
# Use (( )) for integer math — never expr or $[ ]
(( total = count * price ))
(( remainder = total % 7 ))
(( i += 1 ))
(( i-- ))

# Use $(( )) in string contexts
echo "Total: $(( count * price ))"

# Comparison
if (( a > b )); then
  log_info "a is larger"
fi

# Avoid standalone (( )) with set -e when result might be 0 (falsy)
# This exits with set -e when i is 0:  (( i++ ))
# Safe pattern:
(( i++ )) || true
# Or use: i=$(( i + 1 ))
```

---

## Checking External Commands Safely

```bash
# Existence check
if ! command -v docker &>/dev/null; then
  die 2 "docker is required but not installed"
fi

# Version check
docker_version="$(docker --version | grep -oP '\d+\.\d+\.\d+')"
required="20.10.0"
# Compare versions as dot-separated integers
version_ge() {
  local a b
  IFS='.' read -ra a <<< "$1"
  IFS='.' read -ra b <<< "$2"
  for i in 0 1 2; do
    (( ${a[i]:-0} > ${b[i]:-0} )) && return 0
    (( ${a[i]:-0} < ${b[i]:-0} )) && return 1
  done
  return 0
}
version_ge "${docker_version}" "${required}" \
  || die 2 "docker >= ${required} required (found ${docker_version})"
```

---

## Dry-Run Pattern

```bash
#######################################
# Execute a command, or print it if DRY_RUN=true.
# Globals:
#   DRY_RUN
# Arguments:
#   Command and all its arguments
#######################################
run_or_dry() {
  if [[ "${DRY_RUN:-false}" == "true" ]]; then
    log_info "[DRY-RUN] would run: $*"
    return 0
  fi
  "$@"
}

# Usage:
run_or_dry rm -rf "${old_dir}"
run_or_dry kubectl apply -f "${manifest}"
```

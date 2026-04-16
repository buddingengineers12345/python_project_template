# Bandit

Bandit is a security linter for Python. It scans source code for common security issues
using a set of AST-based plugins, each targeting a specific vulnerability class.

---

## What it does

- Statically analyses Python AST for security anti-patterns
- Reports each finding with a severity (LOW / MEDIUM / HIGH) and a confidence
  (LOW / MEDIUM / HIGH) so you can filter by signal strength
- Does **not** execute code — pure static analysis

---

## Installation

```bash
pip install bandit     # or: uv add --dev bandit
```

Verify:
```bash
bandit --version
```

---

## pyproject.toml config (annotated)

Bandit reads a limited set of keys from `[tool.bandit]`. Note that severity/confidence
thresholds must be passed as **CLI flags** — they are not supported as pyproject.toml
keys.

```toml
[tool.bandit]
# Directories or files to scan (passed to -r).
targets = ["src"]

# Test IDs to skip project-wide. Use sparingly — prefer per-line nosec.
# B101 = assert statement (valid in tests; exclude tests dir instead of skipping globally)
# B104 = binding to 0.0.0.0 (acceptable in containerised services — document the reason)
skips = ["B101"]

# Paths to exclude from scanning (regex matched against file path).
exclude_dirs = [".venv", "build", "dist", "tests"]
```

### Severity and confidence thresholds

Thresholds are set via CLI flags, not pyproject.toml:

| CLI flag | Meaning |
|---|---|
| `-l` | Report LOW+ severity (default: all) |
| `-ll` | Report MEDIUM+ severity (recommended) |
| `-lll` | Report HIGH severity only |
| `-i` | Report LOW+ confidence |
| `-ii` | Report MEDIUM+ confidence (recommended) |
| `-iii` | Report HIGH confidence only |

For CI, use `-ll -ii` (MEDIUM/MEDIUM) to filter noise without missing real issues:

```bash
bandit -c pyproject.toml -r src/ -ll -ii
```

---

## Common issue codes and fixes

| Code | Issue | Fix |
|---|---|---|
| `B101` | `assert` statement | Use explicit `if`/`raise` for runtime validation |
| `B105` | Hardcoded password — string literal | Load from env var or secrets manager |
| `B106` | Hardcoded password — function argument default | Use `None` default; load at runtime |
| `B107` | Hardcoded password — function argument | Same as B106 |
| `B108` | Probable insecure temp file | Use `tempfile.mkstemp()` or `tempfile.TemporaryFile()` |
| `B110` | `try/except/pass` — silenced exception | Log or handle the exception explicitly |
| `B201` | Flask debug mode in production | Never set `debug=True` outside local dev |
| `B301` | `pickle` on untrusted data | Use `json` or `msgpack` for untrusted sources |
| `B303` | MD5 / SHA1 for cryptography | Use `hashlib.sha256()` or better |
| `B311` | `random` for security-sensitive use | Use the `secrets` module instead |
| `B324` | Insecure hash function | Use SHA-256+ |
| `B501` | SSL certificate verification disabled | Remove `verify=False` |
| `B601` | `shell=True` in subprocess | Pass a list of args; never interpolate user input |
| `B602` | `subprocess` with shell injection risk | Same as B601 |
| `B608` | SQL string formatting — injection risk | Use parameterised queries |

### Suppressing a finding inline

```python
result = subprocess.run(cmd, shell=True)  # nosec B602
```

Always include the specific code in `# nosec`. A bare `# nosec` suppresses every finding
on the line and makes the reasoning invisible to reviewers.

To suppress a finding project-wide, add it to `skips` in `pyproject.toml` with a comment
explaining why — e.g. `skips = ["B104"]  # service runs in a container; 0.0.0.0 is correct`.

---

## Running bandit

```bash
# Basic scan using pyproject.toml config:
bandit -c pyproject.toml -r src/

# Recommended CI mode — MEDIUM severity and confidence minimum:
bandit -c pyproject.toml -r src/ -ll -ii

# JSON output for downstream tooling or artefact storage:
bandit -c pyproject.toml -r src/ -f json -o bandit-report.json

# Run only specific tests:
bandit -r src/ -t B301,B303
```

Exit codes: `0` = no issues at or above threshold, `1` = issues found, `2` = bandit error.

---

## CI step (GitHub Actions)

```yaml
- name: Install bandit
  run: pip install bandit

- name: Security lint with bandit
  run: bandit -c pyproject.toml -r src/ -ll -ii
```

See `SKILL.md` for the full CI ordering across all tools.

---

## Pre-commit hook entry

```yaml
- repo: https://github.com/PyCQA/bandit
  rev: 1.8.3           # pin to a specific release; update with: pre-commit autoupdate
  hooks:
    - id: bandit
      args: ["-c", "pyproject.toml", "-ll", "-ii"]
      # Scope to src/ only — test code legitimately uses assert, subprocess, etc.
      files: ^src/
```

---

## Gotchas

- **Exclude tests from scanning.** Test code legitimately uses `assert` (B101), raw
  subprocess calls, and sometimes intentionally insecure patterns in fixtures. Add
  `tests` to `exclude_dirs` in `[tool.bandit]` rather than globally skipping B101.
- **Severity thresholds are CLI-only.** You cannot set `severity = "MEDIUM"` in
  `[tool.bandit]` — bandit ignores unknown keys. Pass `-ll -ii` on the command line
  (or in the pre-commit `args`).
- **`# nosec` without a code is an anti-pattern.** Always write `# nosec B601` so
  reviewers know exactly which finding is being suppressed and why.
- **Bandit flags patterns, not intent.** A `random` call used for a non-security shuffle
  will still trigger B311. Add `# nosec B311` with a comment explaining the non-security
  use rather than globally skipping B311.
- **Bandit is not a substitute for a full security audit.** It catches common
  anti-patterns but misses logic-level vulnerabilities, dependency CVEs (use `pip-audit`
  for those), and runtime issues.
- **Overlap with semgrep.** Both tools flag issues like `eval`, insecure hashes, and SQL
  injection. The overlap is intentional — each catches slightly different forms of the
  same pattern. Do not remove bandit in favour of semgrep.

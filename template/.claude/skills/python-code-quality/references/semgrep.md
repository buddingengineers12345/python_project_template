# Semgrep

Semgrep is a fast, multi-language static analysis tool that matches AST-aware code
patterns. It complements bandit: bandit targets a fixed catalogue of Python security
rules, while semgrep lets you use curated registries and write project-specific custom
rules.

---

## What it does

- Matches structural code patterns without executing code
- Ships with curated rule registries (`p/python`, `p/owasp-top-ten`, `p/security-audit`)
- Supports custom rules written in YAML — the main value-add over bandit
- Reports findings with severity, rule ID, file, and line number

---

## Installation

```bash
pip install semgrep     # or: uv add --dev semgrep
```

The PyPI package bundles the semgrep engine — no separate binary needed.

Verify:
```bash
semgrep --version
```

---

## Configuration

Semgrep does **not** read `pyproject.toml`. All configuration lives in `.semgrep.yml`
(or a `.semgrep/` directory) at the project root and is passed via `--config`.

---

## .semgrep.yml (annotated)

```yaml
# .semgrep.yml — rule configuration file at the project root.
#
# Registry packs (p/python etc.) cannot be embedded directly in this file —
# they must be passed via --config on the CLI or in pre-commit args.
# This file is for LOCAL custom rules only.
#
# To use registry packs alongside local rules, pass multiple --config flags:
#   semgrep --config p/python --config p/owasp-top-ten --config .semgrep.yml src/

rules:
  # ── Example custom rule ──────────────────────────────────────────────────
  # Custom rules give semgrep its real advantage over bandit.
  # Save additional rules in .semgrep/rules/<name>.yml and reference them
  # with: semgrep --config .semgrep/rules/ src/

  - id: no-hardcoded-jwt-secret
    patterns:
      - pattern: jwt.encode(..., "$SECRET", ...)
      - pattern-not: jwt.encode(..., os.environ.get(...), ...)
    message: >
      Hardcoded JWT secret. Load the secret from an environment variable
      or secrets manager instead.
    languages: [python]
    severity: ERROR

  - id: no-eval
    pattern: eval(...)
    message: >
      eval() executes arbitrary code. Use ast.literal_eval() for safe
      data parsing, or refactor to avoid dynamic evaluation.
    languages: [python]
    severity: ERROR

  - id: no-print-statements
    pattern: print(...)
    message: Use the logging module instead of print() in production code.
    languages: [python]
    severity: WARNING
    # Only enforce this in src/, not tests — pass `files: ^src/` in pre-commit.
```

### Structuring custom rules

For more than a handful of rules, organise under `.semgrep/rules/`:

```
.semgrep/
├── rules/
│   ├── security.yml        # project-specific security rules
│   ├── style.yml           # project-specific style rules
│   └── tests/              # test fixtures for rules (semgrep --test)
│       └── security_test.py
```

Reference the whole directory: `semgrep --config .semgrep/rules/ src/`

---

## Common registry rule IDs and fixes

These are available via `--config p/python` or `--config p/security-audit`:

| Rule ID | Issue | Fix |
|---|---|---|
| `python.lang.security.audit.exec-detected` | `exec()` call | Refactor to explicit function calls |
| `python.lang.security.audit.eval-detected` | `eval()` call | Use `ast.literal_eval()` for data |
| `python.lang.security.audit.dangerous-system-call` | `os.system()` | Use `subprocess.run(["cmd"], check=True)` |
| `python.lang.security.audit.formatted-sql-query` | SQL via f-string / `%` | Use parameterised queries |
| `python.lang.security.audit.jinja2.autoescape-disabled` | XSS via Jinja2 | Set `autoescape=True` |
| `python.django.security.audit.raw-query` | Django raw SQL | Use the ORM or parameterised `raw()` |
| `python.requests.security.no-auth-over-http` | Credentials over HTTP | Enforce HTTPS |
| `python.lang.security.insecure-hash-use` | MD5 / SHA1 for security | Use SHA-256 or better |

---

## Suppressing a finding

**Inline (single line):**
```python
result = eval(user_input)  # nosemgrep: python.lang.security.audit.eval-detected
```

**Whole file** (add at top of file):
```python
# nosemgrep: python.lang.security.audit.eval-detected
```

Always include the specific rule ID. A bare `# nosemgrep` suppresses all findings on
the line and makes the intent invisible to reviewers.

---

## Running semgrep

```bash
# Run local rules in .semgrep.yml:
semgrep --config .semgrep.yml src/

# Run a registry pack (fetches rules from semgrep.dev on first run, then caches):
semgrep --config p/python src/

# Run multiple sources together:
semgrep --config p/python --config p/owasp-top-ten --config .semgrep.yml src/

# Restrict to ERROR severity only (suppress WARNING / INFO):
semgrep --config p/python --severity ERROR src/

# JSON output for CI artefacts or downstream tooling:
semgrep --config .semgrep.yml --json src/ -o semgrep-report.json

# Test custom rules against fixtures in .semgrep/rules/tests/:
semgrep --test .semgrep/rules/
```

Exit codes: `0` = no findings, `1` = findings found.

---

## CI step (GitHub Actions)

```yaml
- name: Install semgrep
  run: pip install semgrep

# Cache registry rules to avoid re-fetching on every run.
- name: Cache semgrep rules
  uses: actions/cache@v4
  with:
    path: ~/.semgrep/cache
    key: semgrep-${{ hashFiles('.semgrep.yml') }}

# Run registry packs + local rules together.
- name: Semgrep scan
  run: |
    semgrep --config p/python \
            --config p/owasp-top-ten \
            --config .semgrep.yml \
            --severity ERROR \
            src/
```

See `SKILL.md` for the full CI ordering across all tools.

---

## Pre-commit hook entry

```yaml
- repo: https://github.com/semgrep/semgrep
  rev: v1.60.0          # pin to a specific release; update with: pre-commit autoupdate
  hooks:
    - id: semgrep
      # Registry packs can be passed here too.
      args: ["--config", "p/python", "--config", ".semgrep.yml", "--severity", "ERROR"]
      # Scope to src/ only.
      files: ^src/
      # pass_filenames: true is correct for per-file pattern matching.
      # Cross-file taint analysis is not supported in pre-commit mode.
```

---

## Gotchas

- **Registry packs are CLI flags, not YAML rule entries.** You cannot write `- p/python`
  inside a `rules:` block in `.semgrep.yml` — that syntax is invalid. Pass registries
  with `--config p/python` on the command line or in the pre-commit `args`.
- **Registry rules require internet access on first run.** Rules are cached in
  `~/.semgrep/cache`. In an air-gapped CI environment, vendor the rules locally by
  downloading them and adding as local rule files.
- **`p/security-audit` is noisy.** It includes WARNING and INFO findings on top of
  ERROR. Use `--severity ERROR` in CI until the baseline is clean, then broaden.
- **Semgrep is slower than bandit on first run** because it fetches and compiles registry
  rules. Cache `~/.semgrep/cache` in CI to keep subsequent runs fast.
- **Custom rules are the real value-add.** Registry rules catch generic issues; custom
  rules catch your project's specific anti-patterns. Even two or three custom rules
  tailored to your stack are worth writing.
- **`--config auto` changes silently over time.** Auto mode infers rulesets from your
  codebase and will shift as semgrep's auto-detection improves. Use explicit `--config`
  flags in CI for reproducible results.
- **Overlap with bandit is intentional.** Both tools flag `eval`, insecure hashes, and
  SQL injection but via different matching mechanisms. The overlap means issues are
  caught by at least one tool even if the other misses a variant.

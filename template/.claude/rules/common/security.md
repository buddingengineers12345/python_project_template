# Security Guidelines

## Pre-commit security checklist

Before every commit, verify:

- [ ] No hardcoded secrets: API keys, passwords, tokens, private keys.
- [ ] No credentials in comments or docstrings.
- [ ] All user-supplied inputs are validated before use.
- [ ] Parameterised queries used for all database operations (no string-formatted SQL).
- [ ] File paths from user input are sanitised (no path traversal).
- [ ] Error messages do not expose stack traces, internal paths, or configuration values
      to end users.
- [ ] New dependencies are from trusted sources and pinned to specific versions.

The `pre-bash-commit-quality.sh` hook performs a basic automated scan, but it does not
replace manual review.

## Secret management

- **Never** hardcode secrets in source files, configuration, or documentation.
- Use environment variables; load them with a library (e.g. `python-dotenv`) rather
  than direct `os.environ` reads scattered across code.
- Validate that required secrets are present at application startup; fail fast with a
  clear error rather than silently using a default.
- Rotate any secret that may have been exposed. Treat exposure as certain if the secret
  ever appeared in a commit, even briefly.

```python
# Correct: fail fast, clear message
api_key = os.environ["OPENAI_API_KEY"]   # raises KeyError if missing

# Wrong: silent fallback hides misconfiguration
api_key = os.environ.get("OPENAI_API_KEY", "")
```

## Dependency security

- Pin all dependency versions in `pyproject.toml` and commit `uv.lock`.
- Review `dependabot` PRs promptly; do not let them accumulate.
- Run `just security` (if present) or `uv run pip-audit` before major releases.

## Security response protocol

If a security issue is discovered:

1. Stop work on the current feature immediately.
2. Assess severity: can it expose user data, allow privilege escalation, or cause data loss?
3. For **critical** issues: open a private GitHub security advisory, do not discuss in
   public issues.
4. Rotate any exposed secrets before fixing the code.
5. Write a test that reproduces the vulnerability before patching.
6. Review the entire codebase for similar patterns after fixing.

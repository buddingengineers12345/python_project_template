# Security Guidelines

## Pre-commit checklist

Before every commit:

- [ ] No hardcoded secrets (API keys, passwords, tokens, private keys).
- [ ] All user-supplied inputs are validated before use.
- [ ] Parameterised queries used for all database operations.
- [ ] File paths from user input are sanitised (no path traversal).
- [ ] Error messages do not expose internal paths or configuration values.
- [ ] New dependencies are from trusted sources and pinned.

## Secret management

```python
# Correct: fail fast with a clear error if the secret is missing
api_key = os.environ["OPENAI_API_KEY"]

# Wrong: silent fallback masks misconfiguration
api_key = os.environ.get("OPENAI_API_KEY", "")
```

Use `python-dotenv` in development. Never commit `.env` files. Document required
variables in `.env.example` with placeholder values.

## Dependency security

- Pin all dependency versions in `pyproject.toml` and commit `uv.lock`.
- Review Dependabot / Renovate PRs promptly.

## Security response protocol

1. Stop work on the current feature.
2. For critical issues: open a private security advisory, not a public issue.
3. Rotate any exposed secrets before fixing the code.
4. Write a test that reproduces the vulnerability before patching.
5. Search the codebase for similar patterns after fixing.

# Python Security

# applies-to: **/*.py, **/*.pyi

> This file extends [common/security.md](../common/security.md) with Python-specific content.

## Secret management

Load secrets from environment variables; never hardcode them:

```python
import os

# Correct: fails immediately with a clear error if the secret is missing
api_key = os.environ["OPENAI_API_KEY"]

# Wrong: silently falls back to an empty string, masking misconfiguration
api_key = os.environ.get("OPENAI_API_KEY", "")
```

For development, use `python-dotenv` to load a `.env` file that is listed in `.gitignore`:

```python
from dotenv import load_dotenv
load_dotenv()  # reads .env if present; silently skips if absent
api_key = os.environ["OPENAI_API_KEY"]
```

Never commit `.env` files. Add them to `.gitignore` and document required variables in
`.env.example` with placeholder values.

## Input validation

Validate all external inputs at the boundary before passing them into application logic:

```python
# Correct: validate early, raise with context
def process_order(order_id: str) -> Order:
    if not order_id.isalnum():
        raise ValueError(f"Invalid order ID format: {order_id!r}")
    ...

# Wrong: trusting input, using it unvalidated
def process_order(order_id: str) -> Order:
    return db.query(f"SELECT * FROM orders WHERE id = '{order_id}'")
```

## SQL injection prevention

Always use parameterised queries:

```python
# Correct
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))

# Wrong — SQL injection vulnerability
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

## Path traversal prevention

Sanitise file paths from user input:

```python
from pathlib import Path

base_dir = Path("/app/uploads").resolve()
user_path = (base_dir / user_input).resolve()

if not str(user_path).startswith(str(base_dir)):
    raise PermissionError("Path traversal detected")
```

## Static security analysis

Run **bandit** before release to catch common Python security issues:

```bash
uv run bandit -r src/ -ll   # report issues at medium severity and above
```

Bandit is not a substitute for code review, but it catches common patterns like
hardcoded passwords, use of `shell=True` in subprocess calls, and insecure random.

## Subprocess calls

Avoid `shell=True` when calling external processes; it enables shell injection:

```python
import subprocess

# Correct: list form, no shell expansion
result = subprocess.run(["git", "status"], capture_output=True, check=True)

# Wrong: shell=True + user-controlled input = injection
result = subprocess.run(f"git {user_cmd}", shell=True, check=True)
```

## Cryptography

- Do not implement cryptographic primitives. Use `cryptography` or `hashlib` for
  standard algorithms.
- Use `secrets` (stdlib) for generating tokens, not `random`.
- Use bcrypt or Argon2 for password hashing; never SHA-256 or MD5 for passwords.

```python
import secrets
token = secrets.token_urlsafe(32)   # cryptographically secure
```

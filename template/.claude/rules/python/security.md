# Python Security

# applies-to: **/*.py, **/*.pyi

> This file extends [common/security.md](../common/security.md) with Python-specific content.

## Secret management

```python
import os

# Correct: fails immediately with a clear error
api_key = os.environ["OPENAI_API_KEY"]

# Wrong: silent fallback masks misconfiguration
api_key = os.environ.get("OPENAI_API_KEY", "")
```

Use `python-dotenv` for development. Never commit `.env` files.

## Input validation

Validate all external inputs at the boundary:

```python
def process_order(order_id: str) -> Order:
    if not order_id.isalnum():
        raise ValueError(f"Invalid order ID: {order_id!r}")
```

## SQL injection prevention

```python
# Correct
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))

# Wrong — SQL injection vulnerability
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

## Path traversal prevention

```python
from pathlib import Path

base_dir = Path("/app/uploads").resolve()
user_path = (base_dir / user_input).resolve()

if not str(user_path).startswith(str(base_dir)):
    raise PermissionError("Path traversal detected")
```

## Subprocess calls

```python
# Correct: list form, no shell expansion
result = subprocess.run(["git", "status"], capture_output=True, check=True)

# Wrong: shell=True + user input = injection risk
result = subprocess.run(f"git {user_cmd}", shell=True, check=True)
```

## Tokens and random values

```python
import secrets
token = secrets.token_urlsafe(32)   # cryptographically secure
```

Never use `random` for security-sensitive values.

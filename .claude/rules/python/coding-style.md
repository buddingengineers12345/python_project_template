# Python Coding Style

# applies-to: **/*.py, **/*.pyi

> This file extends [common/coding-style.md](../common/coding-style.md) with Python-specific content.

## Formatter and linter

- **ruff** is the single tool for both formatting and linting. Do not use black, isort,
  or flake8 alongside it — they will conflict.
- Run `just fmt` to format, `just lint` to lint, `just fix` to auto-fix safe violations.
- Active rule sets: `E`, `F`, `I`, `UP`, `B`, `SIM`, `C4`, `RUF`, `D`, `C90`, `PERF`.
- Line length: 100 characters. `E501` is disabled (formatter handles wrapping).

## Type annotations

All public functions and methods must have complete type annotations:

```python
# Correct
def calculate_discount(price: float, tier: str) -> float:
    ...

# Wrong — missing annotations
def calculate_discount(price, tier):
    ...
```

- Use `basedpyright` in `standard` mode for type checking (`just type`).
- Prefer `X | Y` union syntax (Python 3.10+) over `Optional[X]` / `Union[X, Y]`.
- Use `from __future__ import annotations` only when needed for forward references in
  Python 3.11; prefer the native syntax.

## Docstrings — Google style

Every public function, class, and method must have a Google-style docstring:

```python
def fetch_user(user_id: int, *, include_deleted: bool = False) -> User | None:
    """Fetch a user by ID from the database.

    Args:
        user_id: The primary key of the user to retrieve.
        include_deleted: When True, soft-deleted users are also returned.

    Returns:
        The matching User instance, or None if not found.

    Raises:
        DatabaseError: If the database connection fails.
    """
```

- `Args`, `Returns`, `Raises`, `Yields`, `Note`, `Example` are the supported sections.
- Test files (`tests/**`) and scripts (`scripts/**`) are exempt from docstring requirements.

## Naming

| Symbol | Convention | Example |
|--------|-----------|---------|
| Module | `snake_case` | `file_manager.py` |
| Class | `PascalCase` | `LoggingManager` |
| Function / method | `snake_case` | `configure_logging()` |
| Variable | `snake_case` | `retry_count` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Type alias | `PascalCase` | `UserId = int` |
| Private | leading `_` | `_internal_helper()` |
| Dunder | `__name__` | `__all__`, `__init__` |

## Immutability

Prefer immutable data structures:

```python
from dataclasses import dataclass
from typing import NamedTuple

@dataclass(frozen=True)
class Config:
    host: str
    port: int

class Point(NamedTuple):
    x: float
    y: float
```

## Error handling

```python
# Correct: specific exception, meaningful message
try:
    result = parse_config(path)
except FileNotFoundError:
    raise ConfigError(f"Config file not found: {path}") from None
except (ValueError, KeyError) as exc:
    raise ConfigError(f"Malformed config: {exc}") from exc

# Wrong: silently swallowed
try:
    result = parse_config(path)
except Exception:
    result = None
```

## Logging

Use **structlog** (configured via `common.logging_manager`). Never use `print()` or the
standard `logging.getLogger()` in application code.

```python
import structlog
log = structlog.get_logger()

log.info("user_created", user_id=user.id, email=user.email)
log.error("payment_failed", order_id=order_id, reason=str(exc), llm=True)
```

## Imports

```python
# Correct order: stdlib → third-party → local
import os
from pathlib import Path

import structlog

from mypackage.common.utils import slugify
```

Avoid wildcard imports (`from module import *`) except in `__init__.py` for re-exporting.

## Collections and comprehensions

Prefer comprehensions over `map`/`filter` for readability:

```python
# Preferred
active_users = [u for u in users if u.is_active]

# Avoid unless the lambda is trivial
active_users = list(filter(lambda u: u.is_active, users))
```

Use generator expressions when you only iterate once and do not need a list in memory.

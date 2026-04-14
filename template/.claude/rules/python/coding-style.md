# Python Coding Style

# applies-to: **/*.py, **/*.pyi

> This file extends [common/coding-style.md](../common/coding-style.md) with Python-specific content.

## Formatter and linter

- **ruff** handles both formatting and linting. Do not use black, isort, or flake8 alongside it.
- Run `just fmt` to format, `just lint` to lint, `just fix` to auto-fix safe violations.
- Active rule sets: `E`, `F`, `I`, `UP`, `B`, `SIM`, `C4`, `RUF`, `TCH`, `PGH`, `PT`, `ARG`,
  `D`, `C90`, `PERF`.
- Line length: 100 characters. `E501` is disabled (formatter handles wrapping).

## Type annotations

All public functions and methods must have complete type annotations:

```python
# Correct
def calculate_discount(price: float, tier: str) -> float: ...

# Wrong
def calculate_discount(price, tier): ...
```

- **basedpyright** strict mode for type checking (`just type`).
- Prefer `X | Y` union syntax over `Optional[X]` / `Union[X, Y]`.

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

Test files (`tests/**`) and scripts (`scripts/**`) are exempt from docstring requirements.

## Naming

| Symbol | Convention | Example |
|--------|-----------|---------|
| Module | `snake_case` | `file_manager.py` |
| Class | `PascalCase` | `LoggingManager` |
| Function / method | `snake_case` | `configure_logging()` |
| Variable | `snake_case` | `retry_count` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Private | leading `_` | `_internal_helper()` |

## Immutability

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

# Wrong: silently swallowed
try:
    result = parse_config(path)
except Exception:
    result = None
```

## Logging

**Mandatory:** use the public APIs in `my_library.common.logging_manager` for all logging
setup and shared log formatting — `configure_logging()`, `get_logger()`, `bind_context()`,
`clear_context()`, `log_section` / `log_sub_section` / `log_section_divider`, `log_fields`,
`log_message`, `wrap_text`, `list_to_numbered_string`, and `write_machine_stdout_line` (raw stdout
for `$(...)` capture only). Call `configure_logging()` once at the app entry point before other
package code logs.

**Event logs:** after `configure_logging()`, use `structlog.get_logger()` and level methods with
event names and keyword fields (no f-strings in the event string).

**Never** in `src/my_library/` (except inside `logging_manager` itself): `print()`,
`logging.getLogger()`, `logging.basicConfig()`, or `structlog.configure()`.

```python
import structlog

from my_library.common.logging_manager import configure_logging

configure_logging()
log = structlog.get_logger()

log.info("user_created", user_id=user.id)
log.error("payment_failed", order_id=order_id, reason=str(exc), llm=True)
```

## Reuse `common/` in package code

Outside `src/my_library/common/`, prefer imports from `my_library.common` (`file_manager`,
`decorators`, `utils`, `logging_manager`) instead of duplicating the same behaviour in `core.py`,
`cli.py`, or other modules.

## Imports

```python
# stdlib → third-party → local
import os
from pathlib import Path

import structlog

from my_library.common.utils import slugify
```

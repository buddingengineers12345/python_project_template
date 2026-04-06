# Python Patterns

# applies-to: **/*.py, **/*.pyi

> This file extends [common/patterns.md](../common/patterns.md) with Python-specific content.

## Dataclasses as data transfer objects

Use `@dataclass` (or `@dataclass(frozen=True)`) for plain data containers.
Use `NamedTuple` when immutability and tuple unpacking are both needed:

```python
from dataclasses import dataclass, field

@dataclass
class CreateOrderRequest:
    user_id: int
    items: list[str] = field(default_factory=list)
    notes: str | None = None

@dataclass(frozen=True)
class Money:
    amount: float
    currency: str = "USD"
```

## Protocol for duck typing

Prefer `Protocol` over abstract base classes for interface definitions:

```python
from typing import Protocol

class Repository(Protocol):
    def find_by_id(self, id: int) -> dict | None: ...
    def save(self, entity: dict) -> dict: ...
    def delete(self, id: int) -> None: ...
```

## Context managers for resource management

Use context managers (`with` statement) for all resources that need cleanup:

```python
# Files
with open(path, encoding="utf-8") as fh:
    content = fh.read()

# Custom resources: implement __enter__ / __exit__ or use @contextmanager
from contextlib import contextmanager

@contextmanager
def managed_connection(url: str):
    conn = connect(url)
    try:
        yield conn
    finally:
        conn.close()
```

## Generators for lazy evaluation

Use generators instead of building full lists when iterating once:

```python
def read_lines(path: Path) -> Generator[str, None, None]:
    with open(path, encoding="utf-8") as fh:
        yield from fh

# Caller controls materialisation
lines = list(read_lines(log_path))           # full list when needed
first_error = next(
    (l for l in read_lines(log_path) if "ERROR" in l), None
)
```

## Dependency injection over globals

Pass dependencies as constructor arguments or function parameters. Avoid module-level
singletons that cannot be replaced in tests:

```python
# Preferred
class OrderService:
    def __init__(self, repo: Repository, logger: BoundLogger) -> None:
        self._repo = repo
        self._log = logger

# Avoid
class OrderService:
    _repo = GlobalRepository()   # hard to test, hard to swap
```

## Configuration objects

Centralise configuration in a typed dataclass or pydantic model loaded once at startup:

```python
@dataclass(frozen=True)
class AppConfig:
    database_url: str
    log_level: str = "INFO"
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            database_url=os.environ["DATABASE_URL"],
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )
```

## Exception hierarchy

Define a project-level base exception and derive domain-specific exceptions from it:

```python
class AppError(Exception):
    """Base class for all application errors."""

class ConfigError(AppError):
    """Raised when configuration is missing or invalid."""

class DatabaseError(AppError):
    """Raised when a database operation fails."""
```

Catch `AppError` at the top level; catch specific subclasses where recovery is possible.

## `__all__` for public API

Define `__all__` in every package `__init__.py` to make the public interface explicit:

```python
# src/mypackage/__init__.py
__all__ = ["AppContext", "configure_logging", "AppError"]
```

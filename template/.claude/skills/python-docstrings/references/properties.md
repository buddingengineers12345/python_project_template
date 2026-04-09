# Property docstrings

Covers: `@property` getters, setters, deleters, and cached properties.

---

## The Core Rule

A `@property` docstring uses **attribute style** — it describes what the
property *is*, not what it *returns*.

```python
# ❌ Wrong — "Returns" phrasing
@property
def butter_sticks(self) -> int:
    """Returns the number of butter sticks we have."""

# ✅ Correct — attribute style
@property
def butter_sticks(self) -> int:
    """The number of butter sticks we have."""
```

Think of it as documenting the *attribute*, not the *method*. The same style
applies regardless of whether the file uses descriptive or imperative style
for regular functions.

---

## Why This Matters

Properties are accessed like attributes (`obj.butter_sticks`, not
`obj.butter_sticks()`). Their docstrings appear in `help()` output alongside
regular attributes. Attribute-style prose is consistent with how users think
about and use properties.

---

## Format

One-liners are typical for simple properties:

```python
@property
def name(self) -> str:
    """The user's full display name."""
    return self._name
```

Use a multi-line docstring only when the property has non-obvious semantics,
side effects, or constraints worth explaining:

```python
@property
def connection(self) -> Connection:
    """The active database connection.

    Lazily established on first access. The connection is reused for
    the lifetime of this instance. Raises RuntimeError if the database
    host is unreachable.
    """
    if self._connection is None:
        self._connection = self._connect()
    return self._connection
```

---

## Setters and Deleters

The `@property` getter carries the primary docstring for the whole
property group. **Setters and deleters do not need separate docstrings**
unless they have distinct behavior worth documenting (e.g., validation
logic, side effects).

```python
@property
def timeout(self) -> float:
    """The connection timeout in seconds. Must be positive."""
    return self._timeout

@timeout.setter
def timeout(self, value: float) -> None:
    # No docstring needed — getter already documents the property
    if value <= 0:
        raise ValueError(f'Timeout must be positive, got {value}.')
    self._timeout = value
```

If the setter has meaningful side effects or validation logic that a caller
must know about, document it:

```python
@timeout.setter
def timeout(self, value: float) -> None:
    """Sets the timeout and resets any in-progress connections.

    Args:
        value: The new timeout in seconds. Must be positive.

    Raises:
        ValueError: If value is not positive.
    """
    if value <= 0:
        raise ValueError(f'Timeout must be positive, got {value}.')
    self._timeout = value
    self._reset_connections()
```

---

## Cached Properties

Document like a regular `@property` — attribute style, describing what the
value is. Mention that the value is cached if that's non-obvious:

```python
from functools import cached_property

@cached_property
def word_count(self) -> int:
    """The total number of words in the document, computed once and cached."""
    return len(self.content.split())
```

---

## Class Docstring vs. Property Docstring

Public `@property` attributes are **not** listed in the class's `Attributes:`
section. They are documented by their own property docstrings.

```python
class Document:
    """A text document with metadata.

    Attributes:
        title: The document's display title.
        content: The raw text content of the document.
        # ← word_count is NOT listed here; it's a @property
    """

    def __init__(self, title: str, content: str):
        self.title = title
        self.content = content

    @cached_property
    def word_count(self) -> int:
        """The total number of words in the document."""
        return len(self.content.split())
```

---

## Quick Reference

| Pattern | Rule |
|---|---|
| Getter | Attribute-style: `"""The X."""` — never `"""Returns the X."""` |
| Setter | No docstring needed unless it has notable side effects or validation |
| Deleter | No docstring needed unless behavior is non-obvious |
| Cached property | Attribute style; mention caching if non-obvious |
| In `Attributes:` section | Do NOT list `@property` attributes there — they document themselves |

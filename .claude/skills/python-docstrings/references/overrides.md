# Overriding method docstrings

Covers: methods that override base class methods, `@override` decorator,
abstract method implementations.

---

## The Core Rule

Whether a docstring is required on an overriding method depends on two things:
1. Whether the `@override` decorator is present
2. Whether the overriding method materially changes the contract

| `@override` present? | Contract changed? | Docstring required? |
|---|---|---|
| ✅ Yes | No | ❌ Not required |
| ✅ Yes | Yes | ✅ Required (document *only the differences*) |
| ❌ No | N/A | ✅ Always required |

---

## `@override` With No Contract Change — Omit the Docstring

When the method is explicitly decorated with `@override` and the behavior is
identical to the base class contract, the docstring may be omitted entirely.
The decorator signals that documentation lives in the base class.

```python
from typing_extensions import override

class Parent:
    def do_something(self) -> None:
        """Performs the standard operation."""
        ...

class Child(Parent):
    @override
    def do_something(self) -> None:
        pass  # ← No docstring needed — @override is sufficient
```

Importing `@override`: use `from typing_extensions import override` (Python < 3.12)
or `from typing import override` (Python 3.12+).

---

## `@override` With Contract Change — Document the Differences

If the overriding method refines the contract, adds side effects, or changes
behavior in ways the caller must know about, provide a docstring that describes
**only the differences** from the base class. Do not repeat the full base
class documentation.

```python
class Parent:
    def process(self, data: bytes) -> bytes:
        """Processes raw data and returns the result.

        Args:
            data: The raw bytes to process.

        Returns:
            The processed bytes.
        """
        ...

class EncryptingChild(Parent):
    @override
    def process(self, data: bytes) -> bytes:
        """Processes data with AES-256 encryption applied before returning.

        Extends the base class behavior by encrypting the result using the
        key provided at construction time.
        """
        result = super().process(data)
        return self._encrypt(result)
```

---

## Without `@override` — Docstring Always Required

If the method does not carry `@override`, readers have no signal that the
docstring lives elsewhere. A docstring is required.

```python
# ❌ No @override, no docstring — reader doesn't know where to look
class Child(Parent):
    def do_something(self) -> None:
        pass

# ✅ Option A: Add the @override decorator
class Child(Parent):
    @override
    def do_something(self) -> None:
        pass  # Docstring now optional

# ✅ Option B: Add a docstring
class Child(Parent):
    def do_something(self) -> None:
        """Performs the standard operation. See base class for full docs."""
        pass

# ✅ Option C: Minimal reference docstring (acceptable)
class Child(Parent):
    def do_something(self) -> None:
        """See base class."""
        pass
```

---

## Implementing Abstract Methods

Abstract method implementations are a specific form of override. Apply the same rules:
- If using `@override`, docstring is optional when contract is unchanged
- If not using `@override`, provide a docstring describing the implementation

```python
from abc import ABC, abstractmethod
from typing_extensions import override

class DataStore(ABC):
    @abstractmethod
    def read(self, key: str) -> bytes | None:
        """Reads a value from the store by key.

        Args:
            key: The unique identifier for the stored item.

        Returns:
            The stored bytes, or None if the key does not exist.
        """

class RedisStore(DataStore):
    @override
    def read(self, key: str) -> bytes | None:
        # No docstring needed — @override + unchanged contract
        return self._client.get(key)
```

If the implementation has behavior the base class doesn't specify (e.g.,
caching, compression, TTL), document those additions:

```python
class CachingRedisStore(DataStore):
    @override
    def read(self, key: str) -> bytes | None:
        """Reads a value, checking an in-memory LRU cache first.

        Results are cached for up to 60 seconds to reduce Redis load.
        Cache misses fall through to the underlying Redis store.
        """
        cached = self._lru.get(key)
        if cached is not None:
            return cached
        value = self._client.get(key)
        if value is not None:
            self._lru.set(key, value, ttl=60)
        return value
```

---

## Where to Import `@override`

```python
# Python 3.12+
from typing import override

# Python 3.8–3.11
from typing_extensions import override
```

---

## Quick Reference

```
Does the method have @override?
├── YES
│   ├── Contract unchanged → No docstring required
│   └── Contract changed   → Docstring required (differences only)
└── NO
    └── Docstring always required
        ├── Full docstring if the method's behavior is non-trivial
        └── At minimum: "See base class." is acceptable
```

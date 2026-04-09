# Class docstrings

Covers: regular classes, dataclasses, abstract classes, mixin classes,
exception subclasses, and `__init__` docstrings.

---

## Where the Docstring Goes

The class docstring goes **directly below the `class` line**, not inside `__init__`.
`__init__` gets its own separate docstring for its parameters.

```python
class MyClass:
    """Docstring describing the class goes here."""  # ← class docstring

    def __init__(self, value: int):
        """Initializes the instance.                 # ← __init__ docstring

        Args:
            value: The initial value.
        """
        self.value = value
```

---

## What the Summary Line Must Describe

The summary describes **what the instance represents** — not the class mechanism,
not when to use it, not "Class that …".

The rule: imagine describing a *single object* of this type. What *is* it?

```python
# ✅ Describes the instance
class CheeseShopAddress:
    """The address of a cheese shop."""

class UserSession:
    """An authenticated session for a single user."""

class RetryPolicy:
    """A configurable policy for retrying failed operations."""

# ❌ Describes the class itself (wrong)
class CheeseShopAddress:
    """Class that describes the address of a cheese shop."""

class UserSession:
    """Used to manage authenticated user sessions."""

class RetryPolicy:
    """Handles the logic for retrying failed operations."""
```

---

## Full Class Docstring Structure

```python
class SampleClass:
    """Summary of what the class instance represents.

    Optional extended description. Can span multiple paragraphs. Explain
    the purpose of the class, key invariants, or important usage notes.

    Attributes:
        attribute_name: Description of what this attribute holds.
        another_attr: Description. Include type only if no annotation.
    """
```

### Attributes section

- Documents **public instance attributes**, set in `__init__` or elsewhere.
- **Excludes** `@property` — properties get their own docstrings.
- Uses the same format and hanging-indent rules as `Args:` in functions.
- If all attributes are `@property` or the class has none, omit the section.

```python
class UserProfile:
    """A user's profile information and account status.

    Attributes:
        username: The user's unique display name.
        email: The user's primary email address.
        is_active: Whether the account is currently active.
        created_at: UTC datetime when the profile was created.
    """

    def __init__(self, username: str, email: str):
        """Initializes a new UserProfile.

        Args:
            username: The user's unique display name.
            email: The user's primary email address.
        """
        self.username = username
        self.email = email
        self.is_active = True
        self.created_at = datetime.utcnow()
```

---

## The `__init__` Docstring

`__init__` gets a standard function docstring. Its `Args:` section documents
the constructor **parameters**, which may or may not match the `Attributes:` names.

Rules:
- Required if `__init__` has non-obvious parameters.
- Use `Args:` for constructor parameters (not `Attributes:`).
- No `Returns:` section — constructors don't return values.

```python
def __init__(self, likes_spam: bool = False):
    """Initializes the instance based on spam preference.

    Args:
        likes_spam: Defines if instance exhibits this preference.
    """
    self.likes_spam = likes_spam
    self.eggs = 0
```

---

## Exception Classes

Exception subclasses follow the same rules as regular classes, with one additional constraint:

**The summary must describe what the exception *represents*, not when it is raised.**

```python
# ✅ Describes what it IS
class OutOfCheeseError(Exception):
    """No more cheese is available."""

class DatabaseConnectionError(Exception):
    """Failure to establish or maintain a database connection."""

class ValidationError(ValueError):
    """An invalid value was provided for a required field."""

# ❌ Describes when it's raised (wrong)
class OutOfCheeseError(Exception):
    """Raised when no more cheese is available."""

class DatabaseConnectionError(Exception):
    """Raised when a database connection cannot be established."""
```

Exception classes with attributes (e.g., error codes, field names) still use
the `Attributes:` section:

```python
class ValidationError(ValueError):
    """An invalid value was provided for a required field.

    Attributes:
        field_name: The name of the field that failed validation.
        invalid_value: The value that was rejected.
    """

    def __init__(self, field_name: str, invalid_value: object):
        """Initializes a ValidationError.

        Args:
            field_name: The name of the field that failed validation.
            invalid_value: The value that was rejected.
        """
        super().__init__(f'Invalid value for {field_name!r}: {invalid_value!r}')
        self.field_name = field_name
        self.invalid_value = invalid_value
```

---

## Dataclasses

Treat the same as regular classes. The class docstring documents the class and
its `Attributes:`. Since dataclass fields are defined at class level, there is
typically no `__init__` to separately document.

```python
from dataclasses import dataclass

@dataclass
class Point:
    """A point in 2D Cartesian space.

    Attributes:
        x: The horizontal coordinate.
        y: The vertical coordinate.
    """
    x: float
    y: float
```

---

## Abstract Classes

Document the abstract class as if describing what any conforming instance would be.
Note the abstract contract in the extended description if useful.

```python
from abc import ABC, abstractmethod

class DataStore(ABC):
    """A persistent store for structured application data.

    Subclasses must implement read(), write(), and delete(). All
    operations are expected to be atomic with respect to the store.
    """

    @abstractmethod
    def read(self, key: str) -> bytes | None:
        """Reads a value from the store by key.

        Args:
            key: The unique identifier for the stored item.

        Returns:
            The stored bytes, or None if the key does not exist.
        """
```

---

## Mixin Classes

Describe what capability the mixin adds to a class that uses it:

```python
class LoggingMixin:
    """Adds structured logging capabilities to any class.

    Provides self.log (a Logger) and helper methods for emitting
    structured log entries at standard severity levels.
    """
```

---

## Complete Example — Before and After

### ❌ Before
```python
class ContactBook:
    """Class for storing contact information."""

    def __init__(self, owner):
        self.owner = owner
        self.contacts = []
```

Problems:
- "Class for …" anti-pattern
- No `Attributes:` section
- `__init__` has no docstring, `owner` has no type hint or explanation

### ✅ After
```python
class ContactBook:
    """A named collection of contact entries owned by a single person.

    Attributes:
        owner: The name or identifier of the book's owner.
        contacts: A list of contact dicts, each with 'name' and 'email' keys.
    """

    def __init__(self, owner: str):
        """Initializes an empty ContactBook.

        Args:
            owner: The name of the person who owns this contact book.
        """
        self.owner = owner
        self.contacts: list[dict] = []
```

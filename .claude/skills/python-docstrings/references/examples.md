# Docstring examples: before & after

Annotated real-world patterns with explanations of every fix.

---

## Table of Contents

1. [Module Docstrings](#module-docstrings)
2. [Simple Functions](#simple-functions)
3. [Complex Functions](#complex-functions)
4. [Generator Functions](#generator-functions)
5. [Properties](#properties)
6. [Classes](#classes)
7. [Exception Classes](#exception-classes)
8. [Overridden Methods](#overridden-methods)
9. [Full Module — Before/After Audit](#full-module-beforeafter-audit)

---

## Module Docstrings

### ❌ Bad
```python
# No docstring at all — file starts with imports
import os
import json
```

### ✅ Good
```python
"""Utilities for reading and writing user configuration files.

Provides functions for loading config from disk, merging with defaults,
and persisting changes. Supports both JSON and TOML formats.

Typical usage example:

  config = load_config('/etc/myapp/config.json')
  config['theme'] = 'dark'
  save_config(config, '/etc/myapp/config.json')
"""

import os
import json
```

---

## Simple Functions

### ❌ Bad — summary not terminated, no period
```python
def greet(name: str) -> str:
    """Greet the user"""
    return f"Hello, {name}!"
```

### ✅ Good
```python
def greet(name: str) -> str:
    """Returns a greeting string for the given name."""
    return f"Hello, {name}!"
```

---

### ❌ Bad — unnecessary Args/Returns when signature is self-explanatory
```python
def add(a: int, b: int) -> int:
    """Adds two integers.

    Args:
        a: The first integer.
        b: The second integer.

    Returns:
        The sum of a and b.
    """
    return a + b
```

### ✅ Good — one-liner is sufficient
```python
def add(a: int, b: int) -> int:
    """Returns the sum of a and b."""
    return a + b
```

---

## Complex Functions

### ❌ Bad — wrong style, missing sections, no hanging indent
```python
def process_batch(items, max_retries=3, timeout=None):
    """
    Processes a batch of items with retry logic.
    items is a list of dicts. Returns a list of results.
    May raise RuntimeError.
    """
    ...
```
**Problems**: Leading blank line inside `"""`, prose mixes args/returns/raises,
no structured sections, no type info (and no annotations).

### ✅ Good
```python
def process_batch(
    items: list[dict],
    max_retries: int = 3,
    timeout: float | None = None,
) -> list[dict]:
    """Processes a batch of items with automatic retry logic.

    Each item is attempted up to max_retries times. Failed items are
    logged and excluded from the returned results.

    Args:
        items: A list of item dicts, each containing at least an 'id'
          and 'payload' key.
        max_retries: Maximum number of retry attempts per item.
          Defaults to 3.
        timeout: Maximum seconds to wait per item. None means no limit.

    Returns:
        A list of result dicts, one per successfully processed item.
        Failed items are omitted.

    Raises:
        RuntimeError: If the batch processor service is unavailable.
    """
    ...
```

---

## Generator Functions

### ❌ Bad — uses Returns: instead of Yields:
```python
def read_lines(filepath: str):
    """Reads lines from a file.

    Returns:
        Each line of the file as a string, stripped of newlines.
    """
    with open(filepath) as f:
        for line in f:
            yield line.rstrip('\n')
```

### ✅ Good
```python
def read_lines(filepath: str) -> Iterator[str]:
    """Reads lines from a file one at a time.

    Yields:
        Each line of the file as a string, stripped of trailing newlines.
    """
    with open(filepath) as f:
        for line in f:
            yield line.rstrip('\n')
```

---

## Properties

### ❌ Bad — uses "Returns" phrasing (wrong style for properties)
```python
@property
def butter_sticks(self) -> int:
    """Returns the number of butter sticks we have."""
    return self._butter_sticks
```

### ✅ Good — attribute-style, no "Returns"
```python
@property
def butter_sticks(self) -> int:
    """The number of butter sticks we have."""
    return self._butter_sticks
```

---

## Classes

### ❌ Bad — says "Class that …", redundant; no Attributes section
```python
class UserProfile:
    """Class that holds information about a user's profile."""

    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email
        self.is_active = True
```

### ✅ Good — describes instance; has Attributes section; __init__ has Args
```python
class UserProfile:
    """A user's profile information and account status.

    Attributes:
        username: The user's unique display name.
        email: The user's primary email address.
        is_active: Whether the account is currently active.
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
```

---

## Exception Classes

### ❌ Bad — describes when raised, not what it represents
```python
class DatabaseConnectionError(Exception):
    """Raised when a database connection cannot be established."""
```

### ✅ Good — describes what the exception represents
```python
class DatabaseConnectionError(Exception):
    """Failure to establish or maintain a database connection."""
```

---

## Overridden Methods

### ❌ Bad — no @override, no docstring
```python
class AdminUser(BaseUser):
    def get_permissions(self):
        return ['read', 'write', 'delete']
```

### ✅ Good option A — add @override (docstring becomes optional)
```python
from typing_extensions import override

class AdminUser(BaseUser):
    @override
    def get_permissions(self) -> list[str]:
        pass  # Contract unchanged — @override is sufficient
```

### ✅ Good option B — no @override, provide docstring
```python
class AdminUser(BaseUser):
    def get_permissions(self) -> list[str]:
        """Returns all permissions including admin-level delete access."""
        return ['read', 'write', 'delete']
```

### ✅ Good option C — @override but with material difference
```python
class AdminUser(BaseUser):
    @override
    def get_permissions(self) -> list[str]:
        """Returns permissions with admin-level delete added.

        Extends the base class to include 'delete' for admin accounts.
        """
        return ['read', 'write', 'delete']
```

---

## Full Module — Before/After Audit

### ❌ Before — multiple issues
```python
import re
from typing import Iterator


# Parse names out of a contact string
def parse_names(contact_str):
    '''parses names'''
    return re.findall(r'[A-Z][a-z]+', contact_str)


def stream_names(contact_str):
    """Streams names.

    Returns:
        Each name found.
    """
    for name in parse_names(contact_str):
        yield name


class ContactBook:
    """Class for storing contact information."""

    def __init__(self, owner):
        self.owner = owner
        self.contacts = []

    @property
    def count(self):
        """Returns the number of contacts."""
        return len(self.contacts)

    def add(self, name: str, email: str) -> None:
        """add a contact"""
        self.contacts.append({'name': name, 'email': email})
```

**Issues identified**:
- No module docstring
- `parse_names` uses `'''` (should be `"""`)
- `parse_names` summary not capitalized, not terminated with period
- `stream_names` uses `Returns:` instead of `Yields:`
- `ContactBook` class says "Class for …" (wrong pattern)
- `ContactBook` missing `Attributes:` section
- `count` property says "Returns the …" (should be attribute style)
- `add` summary not capitalized, not terminated with period

### ✅ After — all issues resolved
```python
"""Utilities for parsing and managing contact information.

Provides tools to extract names from raw contact strings and maintain
a structured contact book per owner.
"""

import re
from typing import Iterator


def parse_names(contact_str: str) -> list[str]:
    """Extracts capitalized names from a contact string.

    Args:
        contact_str: A free-form string potentially containing proper names.

    Returns:
        A list of strings, each a capitalized name found in contact_str.
    """
    return re.findall(r'[A-Z][a-z]+', contact_str)


def stream_names(contact_str: str) -> Iterator[str]:
    """Streams capitalized names from a contact string one at a time.

    Yields:
        Each capitalized name found in contact_str, in order of appearance.
    """
    for name in parse_names(contact_str):
        yield name


class ContactBook:
    """A named collection of contact entries owned by a single person.

    Attributes:
        owner: The name of the person who owns this contact book.
        contacts: A list of contact dicts, each with 'name' and 'email' keys.
    """

    def __init__(self, owner: str):
        """Initializes an empty ContactBook for the given owner.

        Args:
            owner: The name of the person who owns this contact book.
        """
        self.owner = owner
        self.contacts: list[dict] = []

    @property
    def count(self) -> int:
        """The number of contacts currently in the book."""
        return len(self.contacts)

    def add(self, name: str, email: str) -> None:
        """Adds a new contact entry to the book.

        Args:
            name: The contact's display name.
            email: The contact's primary email address.
        """
        self.contacts.append({'name': name, 'email': email})
```

# Auditing Python files for docstring compliance

Use this reference when reviewing an entire file, or when asked to check
whether existing docstrings follow Google style.

---

## Audit Workflow

1. **Scan the file top to bottom** in this order: module → classes → functions/methods
2. **For each construct**, run through the relevant checklist below
3. **Collect all issues** before making edits — don't fix one thing and miss others
4. **Load the specific reference** for each issue type before rewriting

Reference files to load as needed:
- Module issues → `references/modules.md`
- Function/method issues → `references/functions.md`
- Class issues → `references/classes.md`
- Generator issues → `references/generators.md`
- Property issues → `references/properties.md`
- Override issues → `references/overrides.md`

---

## Module-Level Checklist

- [ ] Module docstring present (required for all non-test files)
- [ ] Docstring is the first statement (before imports)
- [ ] Summary line ≤ 80 characters, ends with `.` `?` or `!`
- [ ] If test file: docstring only present when it adds real information

---

## Function / Method Checklist

For each function or method:

- [ ] **Presence**: Docstring present if function is public API, non-trivial, or non-obvious
- [ ] **Format**: Uses `"""`, not `'''` or `"`
- [ ] **Summary**: One line, ≤ 80 chars, ends with `.` `?` or `!`
- [ ] **No blank line** between `def` line and opening `"""`
- [ ] **Blank line** between summary and body (if body exists)
- [ ] **Args section**: Present if parameters are non-obvious or unannotated
- [ ] **Args content**: Each parameter listed; no types duplicated if annotations exist
- [ ] **Returns section**: Present unless returns `None`, or summary already fully covers it
- [ ] **Returns content**: Tuple not documented as multiple return values
- [ ] **Yields vs Returns**: Generator functions use `Yields:`, not `Returns:`
- [ ] **Raises section**: Present if exceptions are part of the interface contract
- [ ] **Raises content**: No API-misuse exceptions documented
- [ ] **Style**: Descriptive or imperative — consistent across the file

---

## Class Checklist

- [ ] Class docstring present
- [ ] Describes what the **instance represents** (not "Class that …")
- [ ] Summary ≤ 80 chars, ends with punctuation
- [ ] `Attributes:` section present for public instance attributes
- [ ] `Attributes:` does NOT include `@property` attributes (those self-document)
- [ ] `__init__` has its own docstring with `Args:` if parameters are non-obvious
- [ ] Exception subclasses: summary describes what it IS, not "Raised when …"

---

## Property Checklist

- [ ] Uses attribute style: `"""The X."""` — not `"""Returns the X."""`
- [ ] Not listed in class `Attributes:` section

---

## Override Checklist

- [ ] Methods without `@override` have a docstring
- [ ] Methods with `@override` and unchanged contract: docstring may be absent
- [ ] Methods with `@override` and changed contract: docstring documents only the differences

---

## Style Consistency Checklist (file-wide)

- [ ] Descriptive vs imperative style is uniform across all functions
- [ ] Hanging indent in `Args:` is consistent (all 2-space or all 4-space)
- [ ] Arg format consistent (inline vs name-on-own-line style)

---

## Complete Before/After Example — Full Module Audit

### ❌ Before (10 issues present)

```python
import re
from typing import Iterator


# Parse names out of a contact string
def parse_names(contact_str):
    '''parses names'''                               # issue 1: ''', lowercase, no period
    return re.findall(r'[A-Z][a-z]+', contact_str)


def stream_names(contact_str):
    """Streams names.

    Returns:                                          # issue 2: Returns: in a generator
        Each name found.
    """
    for name in parse_names(contact_str):
        yield name


class ContactBook:
    """Class for storing contact information."""     # issue 3: "Class for …" anti-pattern
                                                     # issue 4: no Attributes: section
    def __init__(self, owner):                       # issue 5: no __init__ docstring
        self.owner = owner
        self.contacts = []

    @property
    def count(self):
        """Returns the number of contacts."""        # issue 6: "Returns" on @property
        return len(self.contacts)

    def add(self, name: str, email: str) -> None:
        """add a contact"""                          # issue 7: lowercase, no period
        self.contacts.append({'name': name, 'email': email})

    def search(self, query: str) -> list[dict]:
        # issue 8: no docstring on non-trivial public method
        return [c for c in self.contacts if query.lower() in c['name'].lower()]
```

**Plus**: issue 9 — no module docstring; issue 10 — `parse_names` has no `Args:` or `Returns:` and missing type annotations

---

### ✅ After (all issues resolved)

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
        A list of capitalized name strings found in contact_str, in order
        of appearance. Returns an empty list if none are found.
    """
    return re.findall(r'[A-Z][a-z]+', contact_str)


def stream_names(contact_str: str) -> Iterator[str]:
    """Streams capitalized names from a contact string one at a time.

    Args:
        contact_str: A free-form string potentially containing proper names.

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
        """Initializes an empty ContactBook.

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

    def search(self, query: str) -> list[dict]:
        """Returns contacts whose names contain the query string.

        The search is case-insensitive.

        Args:
            query: The substring to search for within contact names.

        Returns:
            A list of matching contact dicts. Returns an empty list if
            no contacts match.
        """
        return [c for c in self.contacts if query.lower() in c['name'].lower()]
```

### Issues resolved summary

| # | Issue | Fix applied |
|---|---|---|
| 1 | `'''`, lowercase summary, no period | Replaced with `"""`, capitalized, added `.` |
| 2 | `Returns:` in generator | Changed to `Yields:` |
| 3 | "Class for …" anti-pattern | Rewritten to describe the instance |
| 4 | No `Attributes:` section | Added `owner` and `contacts` |
| 5 | No `__init__` docstring | Added with `Args:` |
| 6 | `@property` used "Returns" style | Changed to attribute style |
| 7 | Lowercase summary, no period | Fixed capitalization and punctuation |
| 8 | Missing docstring on `search` | Added full docstring |
| 9 | No module docstring | Added at top of file |
| 10 | `parse_names` missing `Args:`/`Returns:` | Added both sections |

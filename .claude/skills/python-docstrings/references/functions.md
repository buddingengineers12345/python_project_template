# Function and method docstrings

Covers: functions, methods, static methods, class methods, abstract methods.
For generators, also load `generators.md`. For `@property`, load `properties.md` instead.

---

## When Is a Docstring Required?

A docstring is **mandatory** if any one condition holds:
- The function is part of the **public API**
- It has **non-trivial size** (more than a few lines)
- It contains **non-obvious logic**

Private helper functions with simple, obvious logic may skip a docstring, but a one-liner is always acceptable and encouraged.

---

## One-Liner Docstrings

Use when the function's purpose is fully captured in a single line.

```python
def double(x: int) -> int:
    """Returns x multiplied by two."""
    return x * 2
```

Rules:
- Opening and closing `"""` on the **same line**
- Ends with `.`, `?`, or `!`
- Summary ≤ 80 characters
- No `Args:` / `Returns:` sections needed when name + signature are self-explanatory

When the summary line starts with "Returns", "Return", "Yields", or "Yield" **and fully describes the return value**, a `Returns:` section is not needed:

```python
def get_username(user_id: int) -> str:
    """Returns the display name for the given user ID."""
    # No Returns: section needed — the summary covers it completely
```

---

## Full Multi-Section Docstring

Use when parameters, return value, or exceptions need explanation beyond the signature.

### Structure
```
"""Summary line — one line, ≤ 80 chars, ends with punctuation.

Optional extended description. Can be multiple paragraphs. Explains
semantics, not implementation, unless implementation details affect usage
(e.g., side effects, mutation of arguments, performance characteristics).

Args:
    param_name: Description.
    another_param: Longer description that wraps onto the next line
      with a 2-space or 4-space hanging indent relative to the param name.

Returns:
    Description of the return value and any semantics not captured by
    the type annotation.

Raises:
    ExceptionType: When and why this is raised.
"""
```

### Section order
1. Summary line
2. (blank line)
3. Extended description (optional)
4. `Args:` (if needed)
5. `Returns:` or `Yields:` (if needed)
6. `Raises:` (if needed)

### Complete canonical example

```python
def fetch_rows(
    table_handle: smalltable.Table,
    keys: Sequence[bytes | str],
    require_all_keys: bool = False,
) -> Mapping[bytes, tuple[str, ...]]:
    """Fetches rows from a Smalltable.

    Retrieves rows pertaining to the given keys from the Table instance
    represented by table_handle. String keys will be UTF-8 encoded.

    Args:
        table_handle: An open smalltable.Table instance.
        keys: A sequence of strings representing the key of each table
          row to fetch. String keys will be UTF-8 encoded.
        require_all_keys: If True only rows with values set for all keys
          will be returned.

    Returns:
        A dict mapping keys to the corresponding table row data fetched.
        Each row is represented as a tuple of strings. For example:

        {b'Serak': ('Rigel VII', 'Preparer'),
         b'Zim': ('Irk', 'Invader')}

        Returned keys are always bytes. If a key is missing from the
        result, that row was not found (require_all_keys must be False).

    Raises:
        IOError: An error occurred accessing the smalltable.
    """
```

---

## The `Args:` Section

### Basic format

```
Args:
    param_name: Description of what this parameter is and how it's used.
    another_param: Description that wraps when it's long, with a hanging
      indent of 2 or 4 spaces beyond the parameter name.
```

**Be consistent**: pick 2-space or 4-space hanging indent and use it throughout the file.

### Alternative style — name on its own line (also valid)

```
Args:
    table_handle:
        An open smalltable.Table instance.
    keys:
        A sequence of strings representing the key of each table row
        to fetch.
```

Pick one style per file.

### *args and **kwargs

List them with their actual sigil:

```
Args:
    *args: Additional positional arguments forwarded to the base handler.
    **kwargs: Keyword arguments forwarded to the base handler.
```

### No type annotations present

Include the type in the description when the function has no type annotations:

```
Args:
    items (list[dict]): A list of item dictionaries to process.
    timeout (float | None): Maximum wait in seconds. None means no limit.
```

### Boolean flags

Describe what both `True` and `False` (or their absence) mean:

```
Args:
    require_all_keys: If True only rows with values set for all keys
      will be returned. Defaults to False.
```

### Parameters mutated as side effects

Call this out explicitly in the `Args:` description:

```
Args:
    results: A list that will be populated in place with matched items.
```

### Optional parameters with semantic meaning to their default

Don't just repeat the default value — explain what it *means*:

```
Args:
    timeout: Maximum seconds to wait per item. Defaults to None, which
      disables the timeout and waits indefinitely.
```

---

## The `Returns:` Section

### When to include
Include `Returns:` when the return value has semantics not obvious from:
- the type annotation alone, or
- the function's name and summary

### When to omit
- Function returns `None`
- The summary line starts with "Return(s)" or "Yield(s)" and fully explains the return value

### Format

```
Returns:
    Description of what is returned. Include semantic meaning,
    not just the type (the annotation already has the type).
```

### Tuple returns — NEVER document as multiple separate values

```python
# ❌ Wrong (NumPy-style, do not use):
# Returns:
#     mat_a: The left singular vectors.
#     mat_b: The right singular vectors.

# ✅ Correct:
# Returns:
#     A tuple (mat_a, mat_b), where mat_a is the left singular vectors
#     matrix and mat_b is the right singular vectors matrix.
```

### Example return with embedded code

```
Returns:
    A dict mapping user IDs to display names. For example:

    {42: 'alice', 99: 'bob'}

    Returns an empty dict if no users are found.
```

---

## The `Raises:` Section

### What to document

List exceptions that are **part of the function's interface contract** — things a reasonable caller should know about and potentially handle.

```
Raises:
    IOError: An error occurred accessing the remote table.
    ValueError: If timeout is negative.
```

### What NOT to document

Do **not** list exceptions caused by **API misuse** (wrong argument types, violated preconditions the caller should never violate). Documenting these makes the misuse behavior part of the contract.

```python
def connect_to_next_port(self, minimum: int) -> int:
    """Connects to the next available port.

    Args:
        minimum: A port value greater or equal to 1024.

    Returns:
        The new minimum port.

    Raises:
        ConnectionError: If no available port is found.
        # ← NOT listed: ValueError for minimum < 1024
        #   That's API misuse, not part of the contract.
    """
    if minimum < 1024:
        raise ValueError(f'Min. port must be at least 1024, not {minimum}.')
    ...
```

### Format
Same hanging-indent style as `Args:`:
`ExceptionName: Description of when and why this is raised.`

---

## Descriptive vs. Imperative Style

Both are valid. **Pick one per file.**

| Style | Example |
|---|---|
| Descriptive | `"""Fetches rows from a Bigtable."""` |
| Imperative | `"""Fetch rows from a Bigtable."""` |

The docstring for a `@property` always uses **attribute style** regardless of the file's convention — see `properties.md`.

---

## Implementation Details in Docstrings

The docstring should describe **what** a function does and **how to call it** — not **how it's implemented**, unless those details affect the caller.

✅ Worth documenting in docstring:
- Side effects (mutates an argument, writes to disk, emits a log)
- Performance characteristics a caller should factor in
- Behavior under specific edge cases (empty input, None, boundary values)

❌ Keep out of docstring (put in inline comments instead):
- Internal algorithm choice ("we use a weighted dict search…")
- Implementation-specific data structures
- Optimization decisions that don't affect API behavior

---

## Edge Case Examples

### Function with no meaningful return value
```python
def log_event(event: str, level: str = 'INFO') -> None:
    """Logs an application event at the specified level.

    Args:
        event: A description of the event that occurred.
        level: The logging level. Must be one of 'DEBUG', 'INFO',
          'WARNING', or 'ERROR'. Defaults to 'INFO'.
    """
```
No `Returns:` section — function returns `None`.

### Function that returns self for chaining
```python
def set_timeout(self, seconds: float) -> 'Builder':
    """Sets the connection timeout and returns self for chaining.

    Args:
        seconds: Maximum seconds to wait for a connection.

    Returns:
        This Builder instance, to allow method chaining.
    """
```

### Classmethod constructor
```python
@classmethod
def from_dict(cls, data: dict[str, Any]) -> 'UserProfile':
    """Creates a UserProfile from a raw dictionary.

    Args:
        data: A dict containing at least 'username' and 'email' keys.

    Returns:
        A new UserProfile instance populated from data.

    Raises:
        KeyError: If 'username' or 'email' is missing from data.
    """
```

### Staticmethod
```python
@staticmethod
def normalize_email(email: str) -> str:
    """Returns the email address lowercased and stripped of whitespace.

    Args:
        email: The raw email string to normalize.

    Returns:
        The normalized email string.
    """
```

# Docstring sections: deep reference

Source: Google Python Style Guide §3.8
https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings

---

## Table of Contents

1. [Args Section](#args-section)
2. [Returns Section](#returns-section)
3. [Yields Section](#yields-section)
4. [Raises Section](#raises-section)
5. [Attributes Section (Classes)](#attributes-section)
6. [Hanging Indent Styles](#hanging-indent-styles)
7. [When to Omit Sections](#when-to-omit-sections)

---

## Args Section

**Header**: `Args:` (ends with colon)

**Hanging indent**: 2 or 4 spaces more than the parameter name. Be consistent within the file.

### Basic format
```
Args:
    param_name: Description of the parameter.
    another_param: Description that is longer and wraps onto the
      next line with a hanging indent relative to param_name.
```

### Rules
- List every parameter by name in the order they appear in the signature.
- Separate name from description with `: ` (colon + space or colon + newline).
- If no type annotation exists, include type in the description:
  `keys (list[str]): A sequence of key strings.`
- If annotations exist, skip the type — don't duplicate it.
- `*args` and `**kwargs` are listed using their actual names including the `*` / `**`:
  ```
  Args:
      *args: Positional arguments forwarded to the base handler.
      **kwargs: Keyword arguments forwarded to the base handler.
  ```

### Alternative style — name on its own line (also valid)
```
Args:
    table_handle:
        An open smalltable.Table instance.
    keys:
        A sequence of strings representing the key of each table row
        to fetch. String keys will be UTF-8 encoded.
```
Pick one style per file.

### Edge cases

**Boolean flags**: Describe the effect of `True` and `False` explicitly.
```
Args:
    require_all_keys: If True only rows with values set for all keys
      will be returned.
```

**Optional parameters**: Describe what happens when not provided, or what
the default means semantically (not just its value).
```
Args:
    timeout: Maximum seconds to wait. Defaults to None, which means
      wait indefinitely.
```

**Parameters that are mutated as side effects**: Mention it here.
```
Args:
    results: A list that will be populated with matched items in place.
```

---

## Returns Section

**Header**: `Returns:` (ends with colon)

**Content**: Describe the semantics of the return value and any type information
not already captured by the type annotation.

```
Returns:
    A dict mapping keys to the corresponding table row data fetched.
    Each row is represented as a tuple of strings. For example:

    {b'Serak': ('Rigel VII', 'Preparer'),
     b'Zim': ('Irk', 'Invader')}

    Returned keys are always bytes.
```

### When to omit
- Function returns `None` only.
- The docstring *starts* with "Return", "Returns", "Yield", or "Yields" **and** that
  opening sentence fully describes the return value.

```python
def get_user_name(user_id: int) -> str:
    """Returns the display name for the given user ID."""
    # Returns: section unnecessary — summary already covers it fully
```

### Tuple returns
**Never** document a tuple as if it were multiple return values. Instead:
```
Returns:
    A tuple (mat_a, mat_b), where mat_a is the left singular vectors
    matrix and mat_b is the right singular vectors matrix.
```

Do not do NumPy-style multi-value documentation for tuples.

### Named tuples / dataclasses
Document the type and its meaning, not the individual fields (those are
documented in the class docstring).
```
Returns:
    A UserProfile namedtuple with the user's display information.
```

---

## Yields Section

**Header**: `Yields:` (used instead of `Returns:` for generators)

Document the *yielded object* (what `next()` returns), not the generator object.

```python
def iter_rows(table: Table) -> Iterator[Row]:
    """Iterates over all rows in the table.

    Yields:
        A Row object for each record, in insertion order.
    """
    for row in table:
        yield row
```

---

## Raises Section

**Header**: `Raises:` (ends with colon)

List exceptions that the caller should expect as part of the function's
*normal interface contract*.

```
Raises:
    IOError: An error occurred accessing the smalltable.
    ValueError: If minimum port is less than 1024.
```

### Format
Same hanging-indent style as `Args:`: `ExceptionName: description.`

### What NOT to document in Raises
- Exceptions raised due to **API misuse** (wrong types, violated preconditions
  that the caller should never violate). Documenting these makes the bad
  behavior part of the public contract.
- Exceptions from `assert` statements.

```python
# The ValueError below should NOT be in the docstring's Raises: section
# because it represents a programming error, not a normal interface outcome.
def connect_to_next_port(self, minimum: int) -> int:
    """Connects to the next available port.

    Args:
        minimum: A port value greater or equal to 1024.

    Returns:
        The new minimum port.

    Raises:
        ConnectionError: If no available port is found.
        # NOT listed: ValueError for minimum < 1024 — that's API misuse
    """
    if minimum < 1024:
        raise ValueError(f'Min. port must be at least 1024, not {minimum}.')
    ...
```

---

## Attributes Section

**Used in**: Class docstrings only.

Documents public instance attributes (not `@property` — those are documented
on the property itself).

```
Attributes:
    likes_spam: A boolean indicating if we like SPAM or not.
    eggs: An integer count of the eggs we have laid.
```

Same format rules as `Args:`. Include type information only when there are no
type annotations.

### What belongs in Attributes vs __init__ Args
- `Attributes:` in the class docstring → documents what's *on the instance* after construction.
- `Args:` in `__init__` docstring → documents the constructor *parameters*.
- These may overlap in name but serve different purposes and should both be present.

---

## Hanging Indent Styles

Two formats are both acceptable. **Choose one per file.**

### Style A — inline description
```python
def f(table_handle, keys, require_all_keys=False):
    """Summary line.

    Args:
        table_handle: An open smalltable.Table instance.
        keys: A sequence of strings representing the key of each table
          row to fetch. String keys will be UTF-8 encoded.
        require_all_keys: If True only rows with values set for all keys
          will be returned.

    Returns:
        A dict mapping keys to the corresponding table row data.

    Raises:
        IOError: An error occurred accessing the smalltable.
    """
```

### Style B — name then indented description
```python
def f(table_handle, keys, require_all_keys=False):
    """Summary line.

    Args:
      table_handle:
        An open smalltable.Table instance.
      keys:
        A sequence of strings representing the key of each table row
        to fetch. String keys will be UTF-8 encoded.
      require_all_keys:
        If True only rows with values set for all keys will be returned.

    Returns:
      A dict mapping keys to the corresponding table row data.

    Raises:
      IOError: An error occurred accessing the smalltable.
    """
```

Note: Style B uses 2-space indent (not 4) for the top-level section items.
Still be consistent within the file.

---

## When to Omit Sections

| Section | Omit when |
|---|---|
| `Args:` | Function has no parameters, or name+signature are entirely self-explanatory |
| `Returns:` | Returns `None`; or summary starts with "Returns/Return/Yield/Yields" and fully describes it |
| `Yields:` | Never omit from a generator unless behavior is obvious from summary |
| `Raises:` | Function raises no exceptions as part of its interface contract |
| `Attributes:` | Class has no public instance attributes |

When **all** sections can be omitted and the function is simple, a one-line docstring is preferred:
```python
def square(x: float) -> float:
    """Returns the square of x."""
    return x * x
```

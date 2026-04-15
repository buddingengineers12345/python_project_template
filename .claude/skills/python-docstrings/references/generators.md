# Generator function docstrings

Covers: functions using `yield`, generator expressions, `yield from`.
Also load `references/functions.md` for full `Args:` and `Raises:` rules.

---

## The Core Rule

Generator functions use **`Yields:`** instead of `Returns:`.

Document the **object yielded by each iteration** (what the caller gets from
`next()`), not the generator object that the function call evaluates to.

```python
# ❌ Wrong — using Returns: in a generator
def stream_rows(table: Table) -> Iterator[Row]:
    """Streams rows from a table.

    Returns:
        Each row as a Row object.
    """
    for row in table:
        yield row


# ✅ Correct
def stream_rows(table: Table) -> Iterator[Row]:
    """Streams rows from a table one at a time.

    Yields:
        A Row object for each record in the table, in insertion order.
    """
    for row in table:
        yield row
```

---

## Full Structure

The docstring for a generator follows the same structure as a regular function,
with `Yields:` replacing `Returns:`:

```
"""Summary line.

Extended description if needed.

Args:
    ...

Yields:
    Description of the yielded value per iteration.

Raises:
    ...
"""
```

---

## What to Document in `Yields:`

Describe:
- What type of object is yielded (if not obvious from the type annotation)
- The semantics of each yielded value — what it represents
- Ordering guarantees, if any
- Whether the generator can yield `None`

```python
def parse_log_entries(filepath: str) -> Iterator[LogEntry]:
    """Parses structured log entries from a log file.

    Skips malformed lines without raising an error; they are logged
    as warnings instead.

    Args:
        filepath: Path to the log file to parse.

    Yields:
        A LogEntry for each successfully parsed line in the file,
        in the order they appear.

    Raises:
        FileNotFoundError: If filepath does not exist.
    """
```

---

## Generators That Also Return a Value

In Python 3, a generator can use `return value` to set `StopIteration.value`.
This is rare. Document it in a note within `Yields:` or a separate `Returns:`
section only if the return value is meaningful to callers.

```python
def bounded_counter(limit: int) -> Generator[int, None, str]:
    """Counts up to a limit and returns a completion message.

    Yields:
        Each integer from 0 up to (but not including) limit.

    Returns:
        The string 'done' after all values are yielded. Only
        accessible via StopIteration.value.
    """
    for i in range(limit):
        yield i
    return 'done'
```

---

## Resource-Managing Generators

If the generator manages an expensive or stateful resource (file handle,
database cursor, network connection), mention it in the extended description.
The recommended pattern is a context manager via `contextlib.contextmanager`:

```python
from contextlib import contextmanager

@contextmanager
def open_connection(host: str, port: int) -> Iterator[Connection]:
    """Opens a managed connection that is automatically closed on exit.

    Intended for use as a context manager:

      with open_connection('db.example.com', 5432) as conn:
          rows = conn.query('SELECT ...')

    Args:
        host: The database host address.
        port: The port number to connect to.

    Yields:
        An open Connection instance, valid only within the with block.

    Raises:
        ConnectionRefusedError: If the host refuses the connection.
    """
    conn = Connection(host, port)
    try:
        yield conn
    finally:
        conn.close()
```

---

## `yield from` Functions

Document the same way as a regular generator. Describe what is ultimately
yielded to the caller — not the sub-generator internals.

```python
def iter_all_records(tables: list[Table]) -> Iterator[Row]:
    """Yields all rows across multiple tables in sequence.

    Args:
        tables: A list of Table instances to iterate over.

    Yields:
        A Row object for each record across all tables, in the
        order the tables are provided.
    """
    for table in tables:
        yield from table.iter_rows()
```

---

## Quick Reference

| Situation | Rule |
|---|---|
| Function uses `yield` | Use `Yields:`, never `Returns:` |
| Function uses `yield from` | Use `Yields:`, document the final yielded object |
| Generator with `return value` | Add `Returns:` only if the return value is meaningful |
| Context manager generator | Document with usage example in extended description |
| Summary line | Describe what the function *does*, not what it yields |

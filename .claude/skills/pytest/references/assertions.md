# Assertion patterns

pytest rewrites `assert` statements to produce detailed failure messages. Plain `assert`
is all you need — no `assertEqual`, `assertIn`, or other helper methods.

## Table of contents

- [Basic assertions](#basic-assertions)
- [Comparing collections](#comparing-collections)
- [Floating-point comparisons](#floating-point-comparisons)
- [Exception testing](#exception-testing)
- [Warning testing](#warning-testing)
- [Output capture](#output-capture)
- [Log capture](#log-capture)
- [Custom failure messages](#custom-failure-messages)
- [What to assert and what not to](#what-to-assert-and-what-not-to)

---

## Basic assertions

```python
# Equality
assert result == expected

# Identity
assert instance is not None

# Truthiness
assert is_valid
assert not has_errors

# Containment
assert "error" in response.text
assert user.id in active_user_ids

# Type checking
assert isinstance(result, Order)
```

When a plain `assert` fails, pytest shows both sides of the comparison, the diff for
collections, and the failing expression. This is usually more informative than custom
messages.

## Comparing collections

pytest shows detailed diffs for lists, dicts, and sets on failure.

```python
# Lists — order matters
assert sorted(result) == ["alice", "bob", "carol"]

# Sets — order does not matter
assert set(result) == {"alice", "bob", "carol"}

# Dicts — shows which keys differ
assert response.json() == {
    "status": "ok",
    "count": 3,
    "items": ["a", "b", "c"],
}

# Subset check for dicts
assert response.json().items() >= {"status": "ok", "count": 3}.items()
```

For large collections, consider asserting on specific properties rather than the entire
structure — it makes failures easier to diagnose and tests less brittle:

```python
# Instead of asserting the entire response dict
assert response.json()["status"] == "ok"
assert len(response.json()["items"]) == 3
```

## Floating-point comparisons

Never use `==` for floats. Use `pytest.approx`:

```python
# Absolute tolerance
assert 0.1 + 0.2 == pytest.approx(0.3)

# Relative tolerance
assert measured_speed == pytest.approx(expected_speed, rel=1e-3)

# Absolute tolerance
assert sensor_reading == pytest.approx(0.0, abs=0.01)

# Works with sequences too
assert [0.1 + 0.2, 0.3 + 0.4] == pytest.approx([0.3, 0.7])
```

## Exception testing

Use `pytest.raises` as a context manager. The `match` parameter accepts a regex.

```python
def test_rejects_negative_quantity():
    with pytest.raises(ValueError, match="must be positive"):
        create_order(quantity=-1)

def test_raises_on_missing_config():
    with pytest.raises(ConfigError) as exc_info:
        load_config("/nonexistent/path")
    assert "not found" in str(exc_info.value)
    assert exc_info.value.path == "/nonexistent/path"
```

The `exc_info` object gives you access to the exception instance, type, and traceback
for more detailed assertions.

### Testing that no exception is raised

Do not write `pytest.raises` to assert that something does *not* raise. Just call the
function — if it raises, the test fails automatically.

```python
# Correct — no special handling needed
def test_handles_empty_input_gracefully():
    result = process(input_data=[])
    assert result == []

# Wrong — this is pointless
def test_does_not_raise():
    try:
        process(input_data=[])
    except Exception:
        pytest.fail("Unexpected exception")
```

## Warning testing

Capture and assert on warnings with `pytest.warns`:

```python
def test_deprecation_warning():
    with pytest.warns(DeprecationWarning, match="use new_function"):
        old_function()
```

## Output capture

The `capsys` fixture captures `stdout` and `stderr`:

```python
def test_prints_greeting(capsys):
    greet("Alice")
    captured = capsys.readouterr()
    assert captured.out == "Hello, Alice!\n"
    assert captured.err == ""
```

For subprocess output, use `capfd` (file descriptor level capture).

## Log capture

The `caplog` fixture captures log records:

```python
import logging

def test_logs_retry_attempt(caplog):
    with caplog.at_level(logging.WARNING):
        retry_operation(max_attempts=3)

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"
    assert "retrying" in caplog.records[0].message
```

You can also filter by logger name:

```python
with caplog.at_level(logging.DEBUG, logger="myapp.orders"):
    place_order()
```

## Custom failure messages

Add a message to `assert` when the default output is not enough context:

```python
assert response.status_code == 200, (
    f"Expected 200 OK but got {response.status_code}. "
    f"Body: {response.text[:200]}"
)
```

Use this sparingly — pytest's introspection is usually sufficient. Custom messages are
most useful when the assertion value alone does not explain *why* it failed.

## What to assert and what not to

### Assert on observable behaviour

Tests should verify what the code *does*, not how it does it internally.

```python
# Good: asserts on the result
def test_discount_applied():
    total = checkout(items=[Item(100)], coupon="SAVE10")
    assert total == 90.0

# Bad: asserts on internal implementation steps
def test_discount_applied():
    cart = Cart()
    cart.add(Item(100))
    cart.apply_coupon("SAVE10")
    assert cart._discount_percentage == 10  # private attribute
    assert cart._coupon_applied is True     # implementation detail
```

### Avoid brittle assertions

```python
# Brittle: exact string match breaks if formatting changes
assert str(error) == "Invalid email: test@"

# Better: match the important part
assert "Invalid email" in str(error)

# Or use match for exceptions
with pytest.raises(ValueError, match="Invalid email"):
    validate("test@")
```

### Multiple related assertions are fine

It is fine to have multiple assertions in one test when they verify different aspects
of the same action. The one-assert-per-test rule is too strict — what matters is that
each test verifies one *behaviour*.

```python
def test_user_creation_returns_complete_user(client):
    response = client.post("/users", json={"name": "Alice"})

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alice"
    assert "id" in data
    assert data["created_at"] is not None
```

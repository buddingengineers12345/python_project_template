# Parametrize and markers

Parametrization lets you run the same test logic against multiple inputs. Markers let
you tag, skip, or configure tests. Together they keep test suites DRY and well-organised.

## Table of contents

- [Basic parametrize](#basic-parametrize)
- [Multiple parameters](#multiple-parameters)
- [Parametrize with IDs](#parametrize-with-ids)
- [Stacking parametrize decorators](#stacking-parametrize-decorators)
- [Fixture parametrization](#fixture-parametrization)
- [Built-in markers: skip and xfail](#built-in-markers-skip-and-xfail)
- [Custom markers](#custom-markers)
- [Registering markers](#registering-markers)

---

## Basic parametrize

`@pytest.mark.parametrize` runs the test once per parameter tuple.

```python
@pytest.mark.parametrize(("input_val", "expected"), [
    (2, 4),
    (0, 0),
    (-3, 9),
    (1.5, 2.25),
])
def test_square(input_val, expected):
    assert square(input_val) == pytest.approx(expected)
```

Each tuple becomes a separate test in the output, so a failure points to the exact input
that broke. This is much better than looping inside a single test, where the first failure
hides the rest.

## Multiple parameters

When testing combinations, use tuples with descriptive names:

```python
@pytest.mark.parametrize(("status_code", "should_retry"), [
    (200, False),
    (429, True),
    (500, True),
    (404, False),
])
def test_retry_decision(status_code: int, should_retry: bool) -> None:
    response = MockResponse(status_code=status_code)
    assert decide_retry(response) == should_retry
```

## Parametrize with IDs

By default, pytest labels each case with the parameter values. For complex objects or
long strings, provide explicit IDs to make output readable.

```python
@pytest.mark.parametrize("payload", [
    pytest.param({"name": "A" * 200}, id="long-name"),
    pytest.param({"name": ""}, id="empty-name"),
    pytest.param({"name": None}, id="null-name"),
])
def test_rejects_invalid_payload(payload):
    with pytest.raises(ValidationError):
        validate(payload)
```

Output becomes `test_rejects_invalid_payload[long-name]` instead of a wall of text.

## Stacking parametrize decorators

Stacking two `@pytest.mark.parametrize` decorators produces the cartesian product of
both parameter sets.

```python
@pytest.mark.parametrize("method", ["GET", "POST", "PUT"])
@pytest.mark.parametrize("auth", ["token", "api_key", None])
def test_endpoint_auth(client, method, auth):
    response = client.request(method, "/resource", auth=auth)
    if auth is None:
        assert response.status_code == 401
    else:
        assert response.status_code in (200, 201)
```

This generates 3 x 3 = 9 test cases. Use this sparingly — the combinatorial explosion
can make test suites slow. Prefer it when the two dimensions are genuinely independent.

## Fixture parametrization

Fixtures themselves can be parametrized. Every test that uses the fixture runs once per
parameter value.

```python
@pytest.fixture(params=["sqlite", "postgres"])
def db_engine(request):
    engine = create_engine(request.param)
    yield engine
    engine.dispose()

def test_can_create_table(db_engine):
    # Runs twice: once with sqlite, once with postgres
    db_engine.execute("CREATE TABLE t (id INT)")
    assert table_exists(db_engine, "t")
```

This is powerful for testing the same behaviour against multiple backends, formats, or
configurations without duplicating tests.

## Built-in markers: skip and xfail

### skip and skipif

Skip a test entirely when it cannot run in the current environment.

```python
import sys
import pytest

@pytest.mark.skip(reason="Waiting on upstream fix #456")
def test_broken_feature():
    ...

@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Uses POSIX-only signal handling",
)
def test_signal_handler():
    ...
```

Use `skip` for unconditional skips (known broken, not yet implemented). Use `skipif`
for platform, version, or dependency conditions.

### xfail

Mark a test as *expected to fail*. The test still runs, but a failure is not reported
as an error.

```python
@pytest.mark.xfail(reason="Bug #789 — parser chokes on nested brackets")
def test_nested_brackets():
    assert parse("[[a]]") == [["a"]]
```

When the bug is fixed and the test starts passing, pytest reports it as `XPASS`
(unexpected pass). Use `strict=True` to make an unexpected pass a hard failure — this
catches the moment when a bug fix lands and you should remove the `xfail`.

```python
@pytest.mark.xfail(strict=True, reason="Bug #789")
def test_nested_brackets():
    ...
```

### skip vs xfail decision guide

| Situation                          | Use         |
|------------------------------------|-------------|
| Test cannot run (missing dep)      | `skipif`    |
| Feature not yet implemented        | `xfail`     |
| Known bug, awaiting fix            | `xfail`     |
| Flaky test, needs investigation    | `xfail(strict=False)` temporarily |
| Platform-specific test             | `skipif`    |

## Custom markers

Create your own markers to categorise tests and run subsets.

```python
# conftest.py or in test files
import pytest

# Usage in tests:
@pytest.mark.slow
def test_full_pipeline():
    ...

@pytest.mark.integration
def test_database_migration():
    ...
```

Run subsets from the command line:

```bash
pytest -m "not slow"            # skip slow tests
pytest -m "integration"         # run only integration tests
pytest -m "not integration"     # skip integration tests
pytest -m "slow and integration"  # both markers
```

## Registering markers

Register custom markers in `pyproject.toml` (or `pytest.ini`) so pytest can warn about
typos. With `strict_markers = true`, an unregistered marker causes an error.

```toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests requiring external resources",
    "unit: marks pure unit tests",
    "e2e: marks end-to-end tests",
]
strict_markers = true
```

This prevents silent typos like `@pytest.mark.integation` from going unnoticed.

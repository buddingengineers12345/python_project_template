# Pytest patterns quick reference

Read this file during Stage 1 (RED) when the `pytest` skill is unavailable or when you need a specific pattern.

---

## Basic test anatomy

```python
def test_<behaviour>_when_<condition>():
    # Arrange
    sut = MyClass(arg=value)

    # Act
    result = sut.method(input)

    # Assert
    assert result == expected
```

Name tests as `test_<what>_<when>` so failures read like specifications.

---

## Fixtures

```python
import pytest

@pytest.fixture
def client():
    return MyClient(base_url="http://localhost")

def test_get_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200
```

Put shared fixtures in `conftest.py` at the package root.

---

## Parametrize

Use when the same behaviour needs to hold for many inputs:

```python
@pytest.mark.parametrize("value,expected", [
    (0,   "zero"),
    (1,   "one"),
    (-1,  "negative"),
])
def test_label(value, expected):
    assert label(value) == expected
```

Prefer parametrize over copy-pasted test functions.

---

## Async tests

```python
import pytest

@pytest.mark.asyncio
async def test_fetch_returns_data(httpx_mock):
    httpx_mock.add_response(json={"ok": True})
    result = await fetch("https://example.com")
    assert result == {"ok": True}
```

Requires `pytest-asyncio`. Add `asyncio_mode = "auto"` to `pyproject.toml` `[tool.pytest.ini_options]` to avoid per-test markers.

---

## Temporary files / directories

```python
def test_writes_output(tmp_path):
    out = tmp_path / "result.txt"
    write_result(out)
    assert out.read_text() == "expected"
```

`tmp_path` is a built-in pytest fixture — prefer it over `tempfile`.

---

## Expecting exceptions

```python
import pytest

def test_raises_on_invalid_input():
    with pytest.raises(ValueError, match="must be positive"):
        process(-1)
```

Always use `match=` to assert the message, not just the type.

---

## Markers

```python
@pytest.mark.slow
def test_integration():
    ...
```

Register custom markers in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
markers = ["slow: marks tests as slow"]
```

---

## Coverage

After GREEN is confirmed, check coverage on the new module:

```bash
python -m pytest --cov=<module> --cov-report=term-missing
```

The new code should appear with 100% (or close) coverage. If not, a test is missing.

---

## Test isolation checklist

- No test should depend on the execution order of other tests.
- No shared mutable state at module level (use fixtures instead).
- Each test sets up its own data and tears it down (or uses `tmp_path` / fixtures with appropriate scope).
- Avoid `time.sleep` — use mocks or `freezegun` for time-dependent code.

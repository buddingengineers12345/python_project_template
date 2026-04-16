# Mocking and test doubles

Mocking replaces real dependencies with controlled substitutes so you can test a unit
in isolation. The key principle: mock at the boundary (the outermost I/O call), not
deep inside the implementation.

## Table of contents

- [When to mock](#when-to-mock)
- [When not to mock](#when-not-to-mock)
- [monkeypatch (built-in)](#monkeypatch-built-in)
- [pytest-mock and the mocker fixture](#pytest-mock-and-the-mocker-fixture)
- [Patching: where to patch](#patching-where-to-patch)
- [Common mock patterns](#common-mock-patterns)
- [Verifying calls](#verifying-calls)

---

## When to mock

Mock when the real dependency would make the test slow, flaky, or non-deterministic:

- **Network calls** — HTTP APIs, email sending, webhooks.
- **Databases** — when you need pure unit isolation (integration tests use the real DB).
- **Filesystem** — though `tmp_path` is often better than mocking.
- **Time** — `datetime.now()`, `time.sleep()` for deterministic testing.
- **External services** — payment processors, cloud APIs, third-party SDKs.

## When not to mock

Mocking too much makes tests pass even when the real code is broken. Avoid mocking:

- **The code under test** — you are testing *it*, not a mock of it.
- **Internal helpers** — mock the external boundary, not the private function that
  calls it. If you mock `_parse_response()` instead of the HTTP call, the test passes
  even if `_parse_response()` has a bug.
- **Data structures and value objects** — use real objects. Mocking a dataclass or
  dict is more confusing than using the real thing.
- **In integration tests** — the whole point is exercising real interactions.

## monkeypatch (built-in)

`monkeypatch` is a pytest fixture that temporarily modifies objects, dictionaries, and
environment variables. Changes are automatically reverted after the test.

### Environment variables

```python
def test_uses_custom_timeout(monkeypatch):
    monkeypatch.setenv("REQUEST_TIMEOUT", "5")
    config = load_config()
    assert config.timeout == 5

def test_fails_without_api_key(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    with pytest.raises(ConfigError, match="API_KEY"):
        load_config()
```

### Object attributes

```python
def test_uses_stub_clock(monkeypatch):
    fixed_time = datetime(2025, 1, 15, 12, 0, 0)
    monkeypatch.setattr("myapp.utils.datetime", lambda: fixed_time)
    assert get_greeting() == "Good afternoon"
```

### Dictionary entries

```python
def test_overrides_setting(monkeypatch):
    monkeypatch.setitem(app_settings, "max_retries", 0)
    with pytest.raises(ServiceError):
        call_with_retry()
```

## pytest-mock and the mocker fixture

`pytest-mock` wraps `unittest.mock` in a fixture called `mocker`. It provides the same
API (`patch`, `MagicMock`, `call`) but automatically cleans up patches after the test.

```python
def test_sends_email_on_signup(mocker):
    mock_send = mocker.patch("myapp.email.send_email")

    register_user(name="Alice", email="alice@example.com")

    mock_send.assert_called_once_with(
        to="alice@example.com",
        subject="Welcome!",
    )
```

### Creating mock objects

```python
def test_handles_api_failure(mocker):
    mock_client = mocker.MagicMock()
    mock_client.get.side_effect = ConnectionError("timeout")

    service = DataService(client=mock_client)
    result = service.fetch_safe(endpoint="/data")

    assert result is None
    mock_client.get.assert_called_once()
```

## Patching: where to patch

A common mistake: patching the wrong location. Patch where the name is *used*, not
where it is *defined*.

```python
# myapp/orders.py
from myapp.email import send_email  # imported into orders module

def place_order(item):
    # ... order logic ...
    send_email(to=user.email, subject="Order placed")
```

```python
# Correct: patch where send_email is looked up
mocker.patch("myapp.orders.send_email")

# Wrong: patching the definition module doesn't affect the import in orders.py
mocker.patch("myapp.email.send_email")
```

The rule: if `orders.py` does `from myapp.email import send_email`, the name
`send_email` lives in the `myapp.orders` namespace. Patch `myapp.orders.send_email`.

If `orders.py` does `import myapp.email` and calls `myapp.email.send_email()`, then
patch `myapp.email.send_email` — the lookup goes through the module object.

## Common mock patterns

### Return values

```python
mock_fetch = mocker.patch("myapp.api.fetch_data")
mock_fetch.return_value = {"status": "ok", "items": [1, 2, 3]}
```

### Side effects (exceptions)

```python
mock_fetch = mocker.patch("myapp.api.fetch_data")
mock_fetch.side_effect = TimeoutError("request timed out")
```

### Side effects (sequential returns)

```python
mock_fetch = mocker.patch("myapp.api.fetch_data")
mock_fetch.side_effect = [
    {"page": 1, "items": [1, 2]},
    {"page": 2, "items": [3]},
    {"page": 3, "items": []},  # signals end of pagination
]
```

### Spying (call through to the real implementation)

```python
spy = mocker.spy(myapp.cache, "invalidate")
do_something_that_invalidates_cache()
spy.assert_called_once_with(key="user:42")
# The real invalidate() was called — spy just observed it
```

### Context managers

```python
mock_open = mocker.patch("builtins.open", mocker.mock_open(read_data="file content"))
result = read_config("/etc/app.conf")
assert result == "file content"
```

## Verifying calls

```python
# Was it called at all?
mock.assert_called()

# Called exactly once?
mock.assert_called_once()

# Called with specific args?
mock.assert_called_with(42, key="value")
mock.assert_called_once_with(42, key="value")

# Called multiple times — check each call
assert mock.call_args_list == [
    mocker.call(1),
    mocker.call(2),
    mocker.call(3),
]

# Was it never called?
mock.assert_not_called()
```

Prefer `assert_called_once_with` over `assert_called_with` — the latter only checks
the *most recent* call and silently ignores extra calls, which can mask bugs.

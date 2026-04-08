# Fixtures

Fixtures are pytest's mechanism for dependency injection. A test declares what it needs
by naming fixture functions as parameters, and pytest handles creation, caching, and
teardown automatically.

## Table of contents

- [Basic fixture pattern](#basic-fixture-pattern)
- [Yield fixtures for teardown](#yield-fixtures-for-teardown)
- [Fixture scopes](#fixture-scopes)
- [Autouse fixtures](#autouse-fixtures)
- [Factory fixtures](#factory-fixtures)
- [Fixture composition](#fixture-composition)
- [conftest.py placement](#conftestpy-placement)
- [Built-in fixtures worth knowing](#built-in-fixtures-worth-knowing)

---

## Basic fixture pattern

A fixture is a function decorated with `@pytest.fixture` that returns (or yields) the
resource a test needs.

```python
@pytest.fixture()
def sample_user():
    return User(name="Alice", email="alice@example.com")

def test_user_has_email(sample_user):
    assert sample_user.email == "alice@example.com"
```

The test declares its dependency by including `sample_user` as a parameter. pytest
resolves it automatically — no imports, no manual calls.

## Yield fixtures for teardown

When a fixture needs cleanup after the test, use `yield` instead of `return`. Code
after `yield` runs as teardown, in reverse fixture order.

```python
@pytest.fixture()
def db_session():
    session = create_session()
    yield session           # test uses session here
    session.rollback()      # runs after the test completes
    session.close()
```

This is cleaner than separate setup/teardown methods because the resource's lifecycle
lives in one place. If the setup raises an exception, teardown is skipped for that
fixture (since the resource was never created).

## Fixture scopes

Scopes control how often a fixture is created and destroyed.

| Scope      | Lifecycle                                             | Use when                                    |
|------------|-------------------------------------------------------|---------------------------------------------|
| `function` | Created fresh for each test (default)                 | Most fixtures — ensures isolation            |
| `class`    | Shared across all tests in a `Test` class             | Grouping related tests with shared state     |
| `module`   | Shared across all tests in a `.py` file               | Expensive setup (e.g. loading test data)     |
| `package`  | Shared across all tests in a directory                | Rare — shared service for a test package     |
| `session`  | Created once for the entire test run                  | Very expensive (e.g. Docker container, DB)   |

```python
@pytest.fixture(scope="module")
def large_dataset():
    # Loaded once per test module, not per test
    return load_csv("testdata/large.csv")
```

**Rule of thumb:** start with `function` scope. Widen the scope only when a fixture is
genuinely expensive and the shared state is safe (read-only or properly isolated).

Wider scopes risk state leaking between tests. If a `module`-scoped fixture returns a
mutable object and one test modifies it, subsequent tests see the modified state. Freeze
or copy the data if sharing mutable objects.

## Autouse fixtures

An `autouse=True` fixture is applied to every test in its scope without being explicitly
requested. Use it for cross-cutting concerns that every test needs.

```python
@pytest.fixture(autouse=True)
def reset_caches():
    """Clear all module-level caches before each test."""
    cache.clear()
    yield
    cache.clear()
```

Use autouse sparingly — it creates invisible dependencies. If only some tests need the
fixture, require them to request it explicitly so the dependency is visible.

Good uses for autouse:

- Clearing global caches or singletons.
- Setting environment variables for a test directory.
- Seeding the random number generator for reproducibility.

## Factory fixtures

When tests need multiple similar objects with slight variations, return a factory
function instead of a single object.

```python
@pytest.fixture()
def make_user():
    """Factory fixture that creates users with sensible defaults."""
    def _make_user(name: str = "Alice", role: str = "member") -> User:
        return User(name=name, role=role, email=f"{name.lower()}@test.com")
    return _make_user

def test_admin_can_delete_posts(make_user):
    admin = make_user(name="Bob", role="admin")
    member = make_user(name="Carol", role="member")
    post = create_post(author=member)
    assert admin.can_delete(post)
```

This avoids fixture explosion (one fixture per variation) and keeps tests expressive.

## Fixture composition

Fixtures can depend on other fixtures. pytest resolves the dependency graph
automatically.

```python
@pytest.fixture()
def db_connection():
    conn = connect_to_test_db()
    yield conn
    conn.close()

@pytest.fixture()
def user_repo(db_connection):
    return UserRepository(db_connection)

@pytest.fixture()
def order_service(user_repo, db_connection):
    return OrderService(user_repo=user_repo, db=db_connection)
```

Each fixture declares its own dependencies. Tests request only the top-level fixture
they need, and pytest ensures everything down the chain is created and torn down in
the right order.

## conftest.py placement

`conftest.py` files define fixtures available to all tests in their directory and
subdirectories. Place them strategically:

```
tests/
    conftest.py              # Fixtures available to ALL tests
    unit/
        conftest.py          # Fixtures only for unit tests
        test_models.py
    integration/
        conftest.py          # Fixtures only for integration tests
        test_api.py
```

Rules:

- A fixture in `tests/conftest.py` is available everywhere under `tests/`.
- A fixture in `tests/unit/conftest.py` is available only to `tests/unit/` tests.
- You do not need to import `conftest.py` — pytest discovers it automatically.
- Avoid putting test functions in `conftest.py`; it is for fixtures and hooks only.

## Built-in fixtures worth knowing

pytest provides several fixtures out of the box.

| Fixture            | What it provides                                          |
|--------------------|-----------------------------------------------------------|
| `tmp_path`         | A fresh `pathlib.Path` temporary directory per test       |
| `tmp_path_factory` | Factory to create multiple temp directories (wider scope) |
| `monkeypatch`      | Safely modify objects, dicts, env vars — auto-reverted    |
| `capsys`           | Capture `stdout`/`stderr` output                         |
| `caplog`           | Capture log records                                       |
| `request`          | Access to the test's metadata (markers, params, etc.)     |
| `pytestconfig`     | Access to the pytest configuration and CLI flags          |

```python
def test_writes_output_file(tmp_path):
    output = tmp_path / "result.txt"
    generate_report(output)
    assert output.read_text().startswith("Report:")

def test_logs_warning_on_retry(caplog):
    with caplog.at_level(logging.WARNING):
        retry_operation()
    assert "retrying" in caplog.text
```

Use `monkeypatch` over `unittest.mock.patch` when you need to modify environment
variables, dictionary entries, or object attributes and want automatic reversal:

```python
def test_reads_setting_from_env(monkeypatch):
    monkeypatch.setenv("MYAPP_SETTING", "fixture-value")
    config = load_config()
    assert config.setting == "fixture-value"
```

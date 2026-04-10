# Advanced patterns reference

Deep-dive reference for complex topics. Load when you need specific examples or decision guidance for:

## Table of Contents
1. [Async Testing](#1-async-testing)
2. [Test Doubles In Depth](#2-test-doubles-in-depth)
3. [conftest.py Structure Guide](#3-conftestpy-structure-guide)
4. [Fixture Scope Decision Tree](#4-fixture-scope-decision-tree)
5. [Property-Based Testing Signals](#5-property-based-testing-signals)

---

## 1. Async Testing

### Setup

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"   # auto-marks all async tests; no @pytest.mark.asyncio needed
```

Or mark individually:
```python
# requires: pip install pytest-asyncio
import pytest

@pytest.mark.asyncio
async def test_fetch_user():
    user = await fetch_user(id=1)
    assert user.name == "Alice"
```

### Common Mistakes

#### ❌ Using `asyncio.run()` inside a test
```python
# Wrong — bypasses pytest-asyncio's event loop management
def test_fetch_user():
    user = asyncio.run(fetch_user(id=1))
    assert user.name == "Alice"

# ✅ Correct
@pytest.mark.asyncio
async def test_fetch_user():
    user = await fetch_user(id=1)
    assert user.name == "Alice"
```

#### ❌ `time.sleep()` in async tests
```python
# Wrong — blocks the event loop, defeats async
@pytest.mark.asyncio
async def test_delayed_notification():
    send_notification(user_id=1)
    time.sleep(1)   # blocks everything
    assert notification_was_sent(user_id=1)

# ✅ Correct
@pytest.mark.asyncio
async def test_delayed_notification():
    send_notification(user_id=1)
    await asyncio.sleep(0)  # yield control; or mock the delay entirely
    assert notification_was_sent(user_id=1)
```

#### ❌ Event loop scope mismatch (pytest-asyncio ≥ 0.21)
```python
# Wrong — session-scoped event_loop with function-scoped async fixtures
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture           # scope="function" (default)
async def db_session():   # will fail: can't use function-scope async fixture with session loop
    async with engine.begin() as conn:
        yield conn

# ✅ Correct — match fixture scopes, or use asyncio_mode="auto" with proper scope declarations
@pytest.fixture(scope="session")
async def db_engine():
    engine = create_async_engine(TEST_DB_URL)
    yield engine
    await engine.dispose()

@pytest.fixture   # function scope — creates a transaction per test
async def db_session(db_engine):
    async with db_engine.begin() as conn:
        yield conn
        await conn.rollback()
```

### Mocking Async Calls

```python
# Mocking an async function
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_sends_email_on_registration(mocker):
    mock_send = mocker.patch("myapp.email.send", new_callable=AsyncMock)
    await register_user("alice@example.com")
    mock_send.assert_called_once_with(to="alice@example.com")
```

---

## 2. Test Doubles In Depth

### The Taxonomy

```
Test Double
├── Stub      — returns canned values; you don't assert on it
├── Mock      — records interactions; you DO assert on it
├── Spy       — wraps real object; records calls; real code runs
└── Fake      — simplified working implementation (in-memory DB, etc.)
```

### When to Use Each

| Scenario | Use |
|---|---|
| Replace external HTTP API response | Stub (just return the expected dict) |
| Verify an email was sent with correct args | Mock (`assert_called_once_with`) |
| Need real cache behavior but also call counts | Spy |
| Replace PostgreSQL in unit tests | Fake (SQLite or dict-based store) |

### Stub Example

```python
# Just need a return value — no assertion on the stub
def test_checkout_calculates_correct_total(mocker):
    mocker.patch("myapp.tax.get_rate", return_value=0.08)  # stub
    total = checkout(Cart(items=[Item(price=100)]))
    assert total == 108.0
```

### Mock Example (assert on it)

```python
# Need to verify the side effect happened
def test_order_confirmation_email_sent(mocker):
    mock_email = mocker.patch("myapp.email.send")  # mock
    place_order(user_id=1, items=["widget"])
    mock_email.assert_called_once_with(
        to="user@example.com",
        subject="Order confirmed",
    )
```

### Spy Example

```python
# Need real behavior AND call verification
def test_cache_is_warmed_on_first_access(mocker):
    spy_cache = mocker.spy(cache, "set")   # real cache.set() runs
    get_user(id=1)                          # first access
    spy_cache.assert_called_once()
    get_user(id=1)                          # second access — should use cache
    spy_cache.assert_called_once()         # still only one set() call
```

### Fake Example

```python
# In-memory fake instead of real PostgreSQL
class FakeUserRepository:
    def __init__(self):
        self._store = {}

    def save(self, user):
        self._store[user.id] = user

    def get(self, user_id):
        return self._store.get(user_id)

def test_user_service_saves_new_user():
    repo = FakeUserRepository()
    service = UserService(repo=repo)
    service.register("alice@example.com")
    assert repo.get(1).email == "alice@example.com"
```

### Spec= on Mocks

Without `spec=`, typos in attribute names silently pass:

```python
# ❌ Typo in method name goes undetected
mock = MagicMock()
mock.sned_email()  # typo — no error raised

# ✅ With spec=, typos raise AttributeError
mock = MagicMock(spec=EmailService)
mock.sned_email()  # AttributeError: Mock object has no attribute 'sned_email'
```

---

## 3. conftest.py Structure Guide

### Placement Rules

```
project/
├── conftest.py          ← session-level fixtures (DB engine, test client)
├── tests/
│   ├── conftest.py      ← fixtures shared across all test subdirectories
│   ├── unit/
│   │   ├── conftest.py  ← fixtures only for unit tests
│   │   └── test_auth.py
│   └── integration/
│       ├── conftest.py  ← fixtures only for integration tests
│       └── test_api.py
```

**Rule of thumb:**
- If a fixture is used in only **one** test file → define it in that file
- If used across **multiple** files in a directory → put it in that directory's `conftest.py`
- If used across **all** tests → root `conftest.py`

### Common conftest.py Patterns

```python
# conftest.py — session-level expensive setup
import pytest
from myapp import create_app
from myapp.db import engine, Base

@pytest.fixture(scope="session")
def app():
    """Create application for the entire test session."""
    app = create_app(config="testing")
    return app

@pytest.fixture(scope="session")
def db(app):
    """Create all tables once per session."""
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(autouse=True)
def db_transaction(db):
    """Wrap each test in a transaction that rolls back."""
    connection = db.connect()
    transaction = connection.begin()
    yield connection
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(app):
    """Fresh test client per test."""
    return app.test_client()
```

### Fixture Visibility

Fixtures in `conftest.py` are automatically available to all tests in the same directory and below — no import needed. This is by pytest design.

---

## 4. Fixture Scope Decision Tree

```
Is the fixture expensive to create? (DB, server, network)
├── YES → Can it be safely shared? (read-only, or reset between uses)
│         ├── YES → scope="session" (create once for all tests)
│         └── NO  → scope="function" with cleanup via yield + rollback
└── NO  → Does it create mutable state?
          ├── YES → scope="function" (default — safest)
          └── NO  → scope="module" if tests in one file share it often
                    scope="function" otherwise (keep it simple)
```

### Cleanup Pattern for Every Scope

```python
# Always use yield + cleanup for fixtures that allocate resources
@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(TEST_DB_URL)
    yield engine
    engine.dispose()          # ← cleanup runs after all tests

@pytest.fixture(scope="function")
def db_session(db_engine):
    conn = db_engine.connect()
    tx = conn.begin()
    yield conn
    tx.rollback()             # ← cleanup runs after each test
    conn.close()
```

---

## 5. Property-Based Testing Signals

[Hypothesis](https://hypothesis.readthedocs.io/) is worth suggesting when you see:

- Tests with many hand-crafted input variations (10+ parametrize cases for the same property)
- Functions that should hold invariants for any input (serialization roundtrips, math properties)
- Parsing/validation functions where edge cases are hard to enumerate

### Signal Pattern → Hypothesis Suggestion

```python
# ❌ Hand-crafting input variations for an invariant
@pytest.mark.parametrize("n", [0, 1, 2, 10, 100, 1000, -1, -100])
def test_abs_is_non_negative(n):
    assert abs(n) >= 0

# ✅ Express the property; let Hypothesis find the edge cases
from hypothesis import given, strategies as st

@given(st.integers())
def test_abs_is_always_non_negative(n):
    assert abs(n) >= 0
```

### Roundtrip Pattern

```python
# If serialize + deserialize should be lossless for any valid input:
from hypothesis import given, strategies as st

@given(st.text())
def test_json_roundtrip(s):
    assert json.loads(json.dumps(s)) == s
```

### When NOT to suggest Hypothesis

- Simple, finite, well-known input spaces (3-4 values)
- Tests that verify specific business logic (not general invariants)
- Teams unfamiliar with property-based testing — note it as an "advanced option"

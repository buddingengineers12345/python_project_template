# Pytest patterns reference

## Table of Contents
1. AAA structure
2. parametrize with ids
3. conftest.py layout
4. Class-based grouping
5. Async testing (pytest-asyncio)
6. Marker registration
7. Useful built-in fixtures

---

## 1 — AAA Structure

Every test body uses three labelled sections. Never write bare `...`.

```python
def test_transfer_debits_source(funded_account, empty_account):  # [A1]
    """Transfer 50 from funded → source balance decreases by 50."""
    # Arrange
    initial_balance = funded_account.balance

    # Act
    transfer_funds(funded_account, empty_account, amount=50)

    # Assert
    assert funded_account.balance == initial_balance - 50
```

For tests that just verify an exception is raised, the pattern still applies:

```python
def test_transfer_raises_on_insufficient_funds(funded_account, empty_account):  # [B1]
    """Amount exceeds balance → raises InsufficientFundsError."""
    # Arrange
    amount = funded_account.balance + 0.01

    # Act / Assert  (combined when pytest.raises wraps the act)
    with pytest.raises(InsufficientFundsError):
        transfer_funds(funded_account, empty_account, amount)
```

---

## 2 — parametrize with ids

Always supply `ids=` so pytest output is readable.

```python
@pytest.mark.parametrize("amount, should_succeed", [
    (99.99,  True),
    (100.00, True),   # exact balance
    (100.01, False),  # one cent over
    (0.01,   True),   # minimum positive
], ids=["under_balance", "exact_balance", "one_cent_over", "minimum"])
@pytest.mark.unit
def test_transfer_boundary_amounts(funded_account, empty_account,
                                   amount, should_succeed):  # [C1]
    """Boundary amounts around balance → succeed or raise correctly."""
    # Arrange
    ...
    # Act
    ...
    # Assert
    ...
```

Output: `PASSED test_transfer_boundary_amounts[exact_balance]`
instead of: `PASSED test_transfer_boundary_amounts[100.0-True]`

For error-code style parametrize where the id is obvious from the value,
use `pytest.param(..., id="...")` inline:

```python
@pytest.mark.parametrize("bad_input", [
    pytest.param("",    id="empty_string"),
    pytest.param(None,  id="none"),
    pytest.param("  ",  id="whitespace_only"),
])
def test_parse_rejects_invalid_input(bad_input):  # [B1]
    ...
```

---

## 3 — conftest.py layout

```
tests/
├── conftest.py          ← project-wide fixtures (DB session, HTTP client)
├── unit/
│   ├── conftest.py      ← unit-specific fixtures
│   └── test_transfer.py
└── integration/
    ├── conftest.py      ← integration-specific fixtures (real DB, containers)
    └── test_transfer_db.py
```

Project-wide conftest example:

```python
# tests/conftest.py
import pytest
from myapp.db import create_engine, Session
from myapp.accounts import Account

@pytest.fixture(scope="session")
def db_engine():
    """In-memory SQLite engine for the full test session."""
    engine = create_engine("sqlite:///:memory:")
    # create tables...
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(db_engine):
    """Transactional DB session; rolls back after each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def make_account():
    """Factory fixture — creates Account objects with custom balance."""
    def _make(balance=100.00, account_id="acc-001"):
        return Account(id=account_id, balance=balance)
    return _make
```

---

## 4 — Class-based grouping

Use when a single subject has 8+ tests, or when you want to share fixtures
via class-level setup. Classes must not inherit from `unittest.TestCase` —
they should be plain classes discovered by pytest.

```python
class TestTransferFunds:
    """All tests for the transfer_funds() function."""

    # ── Happy Path ────────────────────────────────────────────────────────

    def test_debits_source(self, funded_account, empty_account):  # [A1]
        """Transfer 50 → source debited by 50."""
        # Arrange
        ...
        # Act
        ...
        # Assert
        ...

    def test_credits_destination(self, funded_account, empty_account):  # [A2]
        """Transfer 50 → destination credited by 50."""
        ...

    # ── Error Paths ───────────────────────────────────────────────────────

    def test_raises_on_insufficient_funds(self, funded_account):  # [B1]
        ...
```

Fixtures still come from conftest.py — class methods receive them as
parameters the same way plain functions do.

---

## 5 — Async testing (pytest-asyncio)

Install: `pip install pytest-asyncio`

Configure in `pytest.ini` or `pyproject.toml`:

```ini
[pytest]
asyncio_mode = auto   # auto-marks all async tests; avoids per-test decorator
```

Or use per-test marker:

```python
import pytest
import pytest_asyncio

@pytest_asyncio.fixture
async def async_client():
    """Async HTTP test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_create_user_returns_201(async_client):  # [A1]
    """POST /users with valid payload → 201 Created."""
    # Arrange
    payload = {"email": "alice@example.com", "name": "Alice"}
    # Act
    response = await async_client.post("/users", json=payload)
    # Assert
    assert response.status_code == 201
```

When the subject is `async def`, all tests that call it must also be `async`.

---

## 6 — Marker registration

Every custom marker must be registered or pytest emits `PytestUnknownMarkWarning`.

```ini
# pytest.ini  (or [tool.pytest.ini_options] block in pyproject.toml)
[pytest]
markers =
    unit: pure-logic tests with no external I/O
    integration: tests that interact with real or fake external systems
    slow: tests that take longer than ~1 second
    regression: tests added to reproduce a specific bug report
```

Run subsets:
```bash
pytest -m unit            # only unit tests
pytest -m "not slow"      # skip slow tests
pytest -m "unit or regression"
```

---

## 7 — Useful built-in fixtures

| Fixture | Use case |
|---|---|
| `tmp_path` | Provides a `pathlib.Path` temp directory, unique per test |
| `capsys` | Capture stdout/stderr: `capsys.readouterr().out` |
| `caplog` | Capture log records: `caplog.records`, `caplog.text` |
| `monkeypatch` | Patch attributes, env vars, dict entries, sys.path |
| `freezegun` (3rd party) | Freeze `datetime.now()` to a fixed value |

```python
def test_export_writes_csv(tmp_path):  # [E1]
    """export_report() writes a CSV to the given path."""
    # Arrange
    output_file = tmp_path / "report.csv"
    # Act
    ...
    # Assert
    assert output_file.exists()
    assert output_file.read_text().startswith("id,name")
```

# Test doubles reference

A test double is any object that stands in for a real collaborator in a test.
Using the wrong kind of double leads to tests that are either too brittle
(breaking when internals change) or too loose (missing real integration bugs).

## Decision guide

```
Does the test need to verify that a specific call was made?
├── YES → Mock  (or Spy if wrapping a real object)
└── NO
    ├── Does the collaborator have complex behaviour that needs to work?
    │   ├── YES → Fake
    │   └── NO → Stub (simplest; just return canned data)
```

---

## Stub
Returns canned data. Does **not** verify how it was called.
Use when: the test only cares about the output, not whether a call happened.

```python
# Using pytest-mock
def test_get_user_returns_display_name(mocker):  # [A1]
    """get_user() formats the name from the repository response."""
    # Arrange
    mocker.patch(
        "myapp.user_service.user_repo.find_by_id",
        return_value={"id": 1, "first": "Alice", "last": "Smith"},
    )
    # Act
    result = get_user(user_id=1)
    # Assert
    assert result.display_name == "Alice Smith"
```

---

## Mock
Returns canned data **and** records calls so assertions can verify behaviour.
Use when: the test cares that a side-effect occurred (email sent, event
published, DB write attempted).

```python
def test_transfer_publishes_event_on_success(mocker, funded_account, empty_account):  # [E1]
    """Successful transfer → audit event published exactly once."""
    # Arrange
    mock_publish = mocker.patch("myapp.events.publish")

    # Act
    transfer_funds(funded_account, empty_account, amount=50)

    # Assert
    mock_publish.assert_called_once_with(
        "funds.transferred",
        amount=50,
        from_id=funded_account.id,
        to_id=empty_account.id,
    )
```

`assert_called_once_with` is strict — prefer it over `assert_called` when
the exact arguments matter. Use `assert_called_once` (no args) when you only
care that the call happened.

---

## Fake
A working, simplified implementation. Has real behaviour but avoids costly
infrastructure (no network, no disk).
Use when: multiple tests need the collaborator to behave realistically (e.g.
an in-memory repository that supports find/save/delete).

```python
# Fake — lives in tests/fakes.py or conftest.py
class FakeAccountRepository:
    def __init__(self):
        self._store: dict[str, Account] = {}

    def save(self, account: Account) -> None:
        self._store[account.id] = account

    def find_by_id(self, account_id: str) -> Account | None:
        return self._store.get(account_id)

    def exists(self, account_id: str) -> bool:
        return account_id in self._store

@pytest.fixture
def account_repo():
    return FakeAccountRepository()

def test_transfer_persists_both_accounts(account_repo, funded_account, empty_account):  # [E1]
    """After transfer, both accounts are updated in the repository."""
    # Arrange
    account_repo.save(funded_account)
    account_repo.save(empty_account)
    # Act
    transfer_funds(funded_account, empty_account, amount=50, repo=account_repo)
    # Assert
    assert account_repo.find_by_id(funded_account.id).balance == 50
    assert account_repo.find_by_id(empty_account.id).balance == 50
```

---

## Spy
Wraps a real object and records calls without changing behaviour.
Use when: you want to verify interactions but still execute the real logic
(useful for testing logging, metrics, or delegating decorators).

```python
def test_transfer_logs_on_success(mocker, funded_account, empty_account):  # [D1]
    """Successful transfer → INFO log entry emitted."""
    # Arrange — spy on the real logger, don't suppress it
    spy = mocker.spy(logging, "info")

    # Act
    transfer_funds(funded_account, empty_account, amount=50)

    # Assert
    spy.assert_called_once()
    assert "transferred" in spy.call_args[0][0].lower()
```

---

## Tool selection summary

| Situation | Tool | pytest API |
|---|---|---|
| Patch a module-level name / env var | Monkeypatch | `monkeypatch.setattr` / `monkeypatch.setenv` |
| Patch a method on an object | pytest-mock | `mocker.patch.object(obj, "method")` |
| Patch a fully-qualified import path | unittest.mock | `@patch("myapp.module.ClassName")` |
| Verify a side-effect happened | Mock assertion | `mock.assert_called_once_with(...)` |
| Full in-memory substitute | Fake class | custom class, fixture in conftest.py |
| Let real logic run, verify calls | Spy | `mocker.spy(obj, "method")` |

---

## Common mistakes

**Over-mocking:** mocking the subject under test itself. Only mock
*collaborators*, never the thing being tested.

**Asserting call count without reason:** `assert_called_once` is brittle if
the implementation is refactored. Only assert call counts when the count is
part of the contract.

**Shared mock state:** if a mock is defined at module scope or in a
session-scoped fixture, call records accumulate across tests. Always scope
mocks to the individual test (function-scoped fixture or inline `mocker` call).

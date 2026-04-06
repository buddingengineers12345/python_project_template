# Testing Requirements

## Minimum coverage: 80 % (85 % for generated projects)

All new code requires tests. Coverage is measured at the module level; do not lower
an existing module's coverage when making changes.

## Test types required

| Type | Scope | Framework |
|------|-------|-----------|
| Unit | Individual functions, pure logic | pytest |
| Integration | Multi-module flows, I/O boundaries | pytest |
| Template rendering | Copier copy/update output (this repo) | pytest + copier API |

End-to-end tests are added for critical user-facing flows when the project ships a CLI
or HTTP API.

## Test-Driven Development workflow

For new features and bug fixes, follow TDD:

1. Write test — it must **fail** (RED).
2. Write minimal implementation — test must **pass** (GREEN).
3. Refactor for clarity and performance (IMPROVE).
4. Verify coverage did not drop.

Skipping the RED step (writing code before a failing test) is not TDD.

## AAA structure (Arrange-Act-Assert)

```python
def test_calculates_discount_for_premium_users():
    # Arrange
    user = User(tier="premium")
    cart = Cart(items=[Item(price=100)])

    # Act
    total = calculate_total(user, cart)

    # Assert
    assert total == 90  # 10 % discount
```

## Naming conventions

Use descriptive names that read as sentences:

```
test_returns_empty_list_when_no_results_match()
test_raises_value_error_when_email_is_invalid()
test_falls_back_to_default_when_config_is_missing()
```

Avoid: `test_1()`, `test_function()`, `test_ok()`.

## Test isolation

- Tests must not share mutable state. Each test starts from a known baseline.
- Mock external I/O (network, filesystem, clocks) at the boundary, not deep in
  the call stack.
- Do not depend on test execution order. Tests must pass when run individually
  and in any order.

## What not to test

- Implementation details that may change without affecting observable behaviour.
- Third-party library internals.
- Trivial getters/setters with no logic.

## Running tests

```bash
just test           # all tests, quiet
just test-parallel  # parallelised with pytest-xdist
just coverage       # coverage report with missing lines
```

Always run `just ci` before opening a pull request.

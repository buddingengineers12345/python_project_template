# Testing Requirements

## Minimum coverage: 85 %

All new code requires tests. Coverage is measured at the module level; do not lower
an existing module's coverage when making changes.

## Test types required

| Type | Scope |
|------|-------|
| Unit | Individual functions, pure logic |
| Integration | Multi-module flows, I/O boundaries |

## Test-Driven Development workflow

For new features and bug fixes, follow TDD:

1. Write test — it must **fail** (RED). Use `/tdd-red` to validate.
2. Write minimal implementation — test must **pass** (GREEN). Use `/tdd-green` to validate.
3. Refactor for clarity (REFACTOR). Tests must stay green after every change.
4. Validate full CI pipeline (`just ci`). Use `/ci-fix` if anything fails.
5. Verify coverage did not drop.

### GREEN means minimal

In the GREEN phase, write only enough code to make the failing test pass. Do not
add error handling for untested paths, optimisations, or features beyond what the
test requires. Those belong in the next RED cycle or in REFACTOR. Over-engineering
in GREEN violates the TDD contract and introduces untested code.

## AAA structure

```python
def test_calculates_discount_for_premium_users():
    # Arrange
    user = User(tier="premium")
    cart = Cart(items=[Item(price=100)])

    # Act
    total = calculate_total(user, cart)

    # Assert
    assert total == 90
```

## Naming

Use descriptive names that read as sentences:

```
test_returns_empty_list_when_no_results_match()
test_raises_value_error_when_email_is_invalid()
```

## Test isolation

- Tests must not share mutable state.
- Mock external I/O at the boundary.
- Tests must pass when run individually and in any order.

## Running tests

```bash
just test           # all tests, quiet
just test-parallel  # parallelised with pytest-xdist
just coverage       # coverage report with missing lines
just ci             # full pipeline
```

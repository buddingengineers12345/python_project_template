---
name: pytest
description: >-
  Comprehensive guide for writing pytest test cases in Python projects. Use this skill
  whenever you need to write, review, refactor, or improve tests — including unit tests,
  integration tests, fixtures, parametrized tests, mocking, and test organization. Also
  use when the user asks about test coverage, flaky tests, test structure, or any pytest
  feature. Trigger on mentions of: pytest, test cases, test coverage, fixtures, mocking,
  parametrize, TDD, test-driven development, unit test, integration test, conftest, or
  any request to add/improve/fix tests in a Python project.
---

# Pytest Skill

A comprehensive skill for writing clear, maintainable, and thorough pytest test suites.
This file covers the essentials, and the `references/` directory has deep dives on each
topic.

## Quick reference: where to go deeper

| Topic                          | Reference file                                                     |
|--------------------------------|--------------------------------------------------------------------|
| Fixtures (scopes, yield, DI)   | [references/fixtures.md](references/fixtures.md)                   |
| Parametrize and markers        | [references/parametrize-and-markers.md](references/parametrize-and-markers.md) |
| Mocking and test doubles       | [references/mocking.md](references/mocking.md)                    |
| Assertion patterns             | [references/assertions.md](references/assertions.md)               |
| Test types (unit/integration)  | [references/test-types.md](references/test-types.md)               |
| Project layout and naming      | [references/test-organization.md](references/test-organization.md) |
| Anti-patterns and fixes        | [references/anti-patterns.md](references/anti-patterns.md)         |
| CI, coverage, and plugins      | [references/ci-and-plugins.md](references/ci-and-plugins.md)       |

**Bundled scripts** (in `scripts/` — run directly, no need to read them into context):

| Script                 | What it does                                             |
|------------------------|----------------------------------------------------------|
| `find_slow_tests.py`   | Runs pytest, identifies tests exceeding a time threshold |
| `mark_slow_tests.py`   | Adds `@pytest.mark.slow` to the identified slow tests   |

## When to load references

| If the task involves…                   | Load                                            |
|------------------------------------------|-------------------------------------------------|
| Fixture scopes, yield, DI, factories    | `references/fixtures.md`                        |
| Parametrize, custom markers, xfail      | `references/parametrize-and-markers.md`         |
| Mocking, monkeypatch, test doubles      | `references/mocking.md`                         |
| Complex assertions, approx, raises      | `references/assertions.md`                      |
| Unit vs integration vs e2e decisions    | `references/test-types.md`                      |
| Project layout, naming, conftest        | `references/test-organization.md`               |
| Debugging flaky tests, common mistakes  | `references/anti-patterns.md`                   |
| CI config, coverage, plugins            | `references/ci-and-plugins.md`                  |
| Simple test writing (default)           | No reference needed — use inline guidance below |

---

## Core principles

### Every test follows Arrange-Act-Assert

Split each test into three clear phases. The separation makes tests readable at a glance
and keeps each test focused on one behaviour.

```python
def test_cart_applies_discount_for_premium_user(premium_user, empty_cart):
    # Arrange
    empty_cart.add_item(Item(price=100))

    # Act
    total = empty_cart.checkout(premium_user)

    # Assert
    assert total == 90.0  # 10% premium discount
```

Put heavy setup into fixtures so the test body stays short — ideally just the Act and
Assert phases are visible.

### Name tests as sentences

A test name should read like a specification. Someone scanning the test file should
understand *what the system does* without reading the body.

```python
# Good — reads as a behaviour spec
def test_returns_empty_list_when_no_results_match(): ...
def test_raises_value_error_for_negative_quantity(): ...
def test_sends_welcome_email_after_registration(): ...

# Bad — vague, no intent
def test_search(): ...
def test_1(): ...
def test_edge_case(): ...
```

### Use plain assert

pytest rewrites `assert` statements to show rich diffs on failure. There is no need for
`assertEqual`, `assertTrue`, or any other assertion method.

```python
assert result == expected
assert "error" in response.text
assert len(items) == 3
```

For floating-point comparisons, use `pytest.approx()`:

```python
assert calculate_pi() == pytest.approx(3.14159, rel=1e-4)
```

For exceptions, use `pytest.raises`:

```python
with pytest.raises(ValueError, match="must be positive"):
    create_order(quantity=-1)
```

### Fixtures over setup methods

pytest fixtures replace xUnit-style `setUp`/`tearDown`. They are more flexible because
tests declare exactly which fixtures they need, and fixtures compose naturally.

```python
# conftest.py
@pytest.fixture()
def db_connection():
    conn = create_test_db()
    yield conn
    conn.rollback()
    conn.close()

@pytest.fixture()
def user_repo(db_connection):
    return UserRepository(db_connection)

# test_users.py
def test_creates_user(user_repo):
    user = user_repo.create(name="Alice")
    assert user_repo.find_by_id(user.id).name == "Alice"
```

Key rules for fixtures:

- Put shared fixtures in `conftest.py` (per-directory or at the test root).
- Use `function` scope (the default) unless the fixture is expensive and safe to share.
- Use `yield` for setup + teardown in a single function.
- Use `tmp_path` for filesystem operations — never hardcode `/tmp` paths.

For advanced fixture patterns, read [references/fixtures.md](references/fixtures.md) for scopes, autouse, factory
fixtures, and advanced patterns.

### Parametrize to cover multiple inputs

When the same logic applies to several inputs, use `@pytest.mark.parametrize` instead
of writing separate test functions or looping inside a test.

```python
@pytest.mark.parametrize(("email", "is_valid"), [
    ("alice@example.com", True),
    ("bob.example.com", False),
    ("@nope", False),
    ("a@b.co", True),
])
def test_email_validation(email: str, is_valid: bool) -> None:
    assert validate_email(email) == is_valid
```

Each parameter set runs as a separate test, so failures are pinpointed. For advanced parametrization, read
[references/parametrize-and-markers.md](references/parametrize-and-markers.md) for
advanced parametrization and custom markers.

### Mock at the boundary

When a test needs to isolate from external systems (network, database, filesystem,
clock), mock the outermost I/O call — not internal helpers.

```python
def test_sends_notification_on_order(mocker):
    # Mock the external email service, not internal logic
    mock_send = mocker.patch("myapp.notifications.email_client.send")

    place_order(item="widget", email="alice@example.com")

    mock_send.assert_called_once_with(
        to="alice@example.com",
        subject="Order confirmed",
    )
```

For advanced mocking patterns, read [references/mocking.md](references/mocking.md) for `monkeypatch`, `pytest-mock`,
factory patterns, and when *not* to mock.

### Test isolation is non-negotiable

Every test must pass when run alone and in any order. Common violations:

- Tests that depend on another test creating data first.
- Tests that share a module-level mutable variable.
- Tests that write to a fixed file path without cleanup.

Use fixtures to provide fresh state. Use `tmp_path` for files. Use `monkeypatch.setenv`
for environment variables. Reset any global state in teardown.

---

## Workflow for writing tests

1. **Identify the behaviour** you want to verify. One test, one behaviour.
2. **Write the test first** (TDD: Red-Green-Refactor).
3. **Run it and confirm it fails** for the right reason.
4. **Write the minimal implementation** to make it pass.
5. **Refactor** both the code and the test for clarity.
6. **Check coverage** — aim for the project threshold (85%).

When adding tests to existing code (not TDD), still follow steps 1 and 5. Focus on
observable behaviour, not implementation details.

---

## File and directory conventions

```
tests/
    conftest.py              # Root-level shared fixtures
    test_imports.py          # Import smoke tests
    unit/
        conftest.py          # Fixtures for unit tests
        test_core.py         # Tests for src/<pkg>/core.py
        test_cli.py          # Tests for src/<pkg>/cli.py
        common/
            conftest.py      # Fixtures for common module tests
            test_utils.py    # Tests for src/<pkg>/common/utils.py
    integration/
        conftest.py          # Fixtures for integration tests
        test_*.py
    e2e/
        conftest.py          # Fixtures for e2e tests
        test_*.py
```

- File names: `test_<module>.py` — mirrors the source module being tested.
- Function names: `test_<behaviour_description>` — snake_case, descriptive.
- Class names: `TestClassName` — group related tests, no `__init__`.
- Fixture names: descriptive nouns (`db_connection`, `sample_user`, `tmp_config_file`).

Read [references/test-organization.md](references/test-organization.md) for the full
project layout (unit/integration/e2e subdirectories), naming rules, and discovery configuration.

---

## Running tests

```bash
just test              # all tests, quiet output
just test-parallel     # parallel with pytest-xdist
just coverage          # coverage report with missing lines
just ci                # full pipeline: lint, type-check, test, etc.
```

Useful pytest CLI flags for development:

```bash
pytest -x                    # stop on first failure
pytest --lf                  # rerun only last-failed tests
pytest -k "email"            # run tests matching keyword
pytest -m "not slow"         # skip tests marked @pytest.mark.slow
pytest --durations=10        # show 10 slowest tests
```

---

## Finding and marking slow tests

Long-running tests slow down the feedback loop. The skill bundles two scripts that
work together to find slow tests and add `@pytest.mark.slow` so they can be skipped
during fast development iterations.

### Step 1: Find slow tests

Run the finder script from your project root. It executes pytest with `--durations=0`
and reports every test whose call phase exceeds the threshold (default: 1 second).

```bash
python <skill-path>/scripts/find_slow_tests.py --threshold 1.0
```

Options:

- `--threshold 0.5` — flag tests slower than 500ms.
- `--top 10` — only show the 10 slowest.
- `--test-path tests/integration/` — limit to a specific directory.
- `--json-only` — machine-readable JSON on stdout only.

The output is a JSON array on stdout (for piping) plus a human summary on stderr.
Both scripts use the standard library `logging` module (stderr for messages; a dedicated
stdout logger for JSON) instead of `print` or raw `sys.stdout`/`sys.stderr` writes.

### Step 2: Mark them

Pipe the output directly into the marker script:

```bash
python <skill-path>/scripts/find_slow_tests.py --threshold 1.0 \
  | python <skill-path>/scripts/mark_slow_tests.py
```

This adds `@pytest.mark.slow` above each slow test function and inserts
`import pytest` if the file does not already have it. Tests that already carry
the marker are skipped.

Use `--dry-run` to preview changes without modifying files:

```bash
python <skill-path>/scripts/find_slow_tests.py --threshold 1.0 \
  | python <skill-path>/scripts/mark_slow_tests.py --dry-run
```

### Step 3: Run fast tests only

Once slow tests are marked, skip them during normal development:

```bash
pytest -m "not slow"
```

Run the full suite (including slow tests) before opening a PR or in CI.

### When to use this

- After adding integration or E2E tests that touch real databases, networks, or
  large datasets.
- When `pytest --durations=10` shows tests taking more than a second.
- During CI optimisation — split fast and slow test runs into separate jobs.

Read [references/parametrize-and-markers.md](references/parametrize-and-markers.md)
for more on custom markers and [references/ci-and-plugins.md](references/ci-and-plugins.md)
for CI integration patterns.

---

## Efficiency: batch edits and parallel calls

- **Batch edits:** When adding multiple test functions to the same file, write
  them all in a single Edit tool call rather than one function at a time.
- **Parallel calls:** When running `just test` and `just coverage` independently,
  make both calls in a single message.
- **Read before edit:** Read the target test file and the source module once each,
  plan all test functions, then write them in one Edit call.

---

## Checklist before committing tests

- [ ] Each test has a clear, descriptive name.
- [ ] Tests follow Arrange-Act-Assert structure.
- [ ] No test depends on another test's side effects.
- [ ] Fixtures handle setup and teardown (no leftover state).
- [ ] External I/O is mocked or uses `tmp_path`.
- [ ] Parametrize is used where multiple inputs test the same logic.
- [ ] Slow tests (>1s) are marked with `@pytest.mark.slow`.
- [ ] Coverage threshold is met for new and modified modules.
- [ ] `just test` passes locally.

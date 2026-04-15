# Test organization

Good test organization makes it easy to find, run, and maintain tests as the project
grows. This document covers layout, naming, discovery, and configuration.

## Table of contents

- [Directory layout](#directory-layout)
- [File naming and discovery](#file-naming-and-discovery)
- [Function and class naming](#function-and-class-naming)
- [Separating test types](#separating-test-types)
- [conftest.py hierarchy](#conftestpy-hierarchy)
- [pytest configuration](#pytest-configuration)

---

## Directory layout

Keep tests in a top-level `tests/` directory, separate from `src/`. Organise tests by type
into subdirectories: `unit/`, `integration/`, and `e2e/`.

```
project/
    src/
        myapp/
            __init__.py
            core.py
            cli.py
            common/
                __init__.py
                utils.py
                decorators.py
                logging_manager.py
    tests/
        conftest.py              # Global fixtures shared by all tests
        test_imports.py          # Import smoke tests
        unit/
            conftest.py          # Fixtures for unit tests
            test_core.py         # Tests for src/myapp/core.py
            test_cli.py          # Tests for src/myapp/cli.py
            common/
                conftest.py      # Fixtures for common module tests
                test_utils.py    # Tests for src/myapp/common/utils.py
                test_decorators.py
                test_logging_manager.py
        integration/
            conftest.py          # Fixtures for integration tests
            test_*.py
        e2e/
            conftest.py          # Fixtures for e2e tests
            test_*.py
```

This layout makes it easy to run subsets:

```bash
pytest tests/unit/          # fast unit tests only
pytest tests/integration/   # integration tests only
pytest tests/e2e/           # end-to-end tests only
```

## File naming and discovery

pytest discovers tests using these rules:

- Searches directories recursively starting from `testpaths` (defaults to current dir).
- Collects files matching `python_files` pattern (default: `test_*.py` or `*_test.py`).
- Within those files, collects functions matching `python_functions` (default: `test_*`).
- Within classes matching `python_classes` (default: `Test*`, no `__init__` method).

**Stick with the defaults.** Name files `test_<module>.py` and functions `test_<behaviour>`.
There is rarely a reason to customise the patterns.

## Function and class naming

### Test functions

Name tests to describe the behaviour, not the implementation. A good test name reads
like a sentence when prefixed with "it":

```python
# Pattern: test_<action>_<condition>_<expectation>
def test_returns_none_when_user_not_found(): ...
def test_raises_validation_error_for_empty_name(): ...
def test_applies_bulk_discount_above_ten_items(): ...
def test_sends_notification_after_order_placed(): ...
```

Avoid generic names like `test_function`, `test_success`, `test_error`. If you cannot
name the test descriptively, you may not be clear on what behaviour you are testing.

### Test classes

Use classes to group related tests. No `__init__` method — pytest skips classes with one.

```python
class TestUserRegistration:
    def test_creates_user_with_valid_data(self, client): ...
    def test_rejects_duplicate_email(self, client): ...
    def test_hashes_password_before_storing(self, db): ...
    def test_sends_welcome_email(self, mocker): ...
```

Classes are optional — flat functions work well for most projects. Use classes when a
group of tests shares a logical context or when you want class-scoped fixtures.

### Fixture naming

Name fixtures as nouns describing what they provide:

```python
@pytest.fixture()
def sample_user(): ...          # a user object

@pytest.fixture()
def db_session(): ...           # a database session

@pytest.fixture()
def populated_cart(): ...       # a cart with items already in it

@pytest.fixture()
def make_invoice(): ...         # a factory for creating invoices
```

Avoid naming fixtures after actions (`setup_database`, `create_user`) — that describes
the implementation rather than the value the test receives.

## Separating test types

Tests are organised by type into subdirectories under `tests/`:

```
tests/unit/           → pytest tests/unit
tests/integration/    → pytest tests/integration
tests/e2e/            → pytest tests/e2e
```

Additionally, use markers for cross-cutting concerns and for running subsets by marker:

```python
@pytest.mark.unit
def test_pure_calculation(): ...

@pytest.mark.integration
def test_database_query(): ...
```

```bash
pytest -m unit                # run only unit tests
pytest -m "not integration"   # skip integration tests
```

Set `pytestmark` at module level in every test file — typically matching the directory
the file lives in (e.g. `pytestmark = pytest.mark.unit` for files in `tests/unit/`).

## conftest.py hierarchy

`conftest.py` files form a hierarchy. Fixtures defined higher in the tree are available
to tests deeper in the tree.

```
tests/
    conftest.py              # Available to ALL tests
        → db_engine, make_user, app_config
    unit/
        conftest.py          # Available to tests/unit/ only
            → mock_db, isolated_config
        common/
            conftest.py      # Available to tests/unit/common/ only
    integration/
        conftest.py          # Available to tests/integration/ only
            → real_db_session, test_server
    e2e/
        conftest.py          # Available to tests/e2e/ only
```

Rules:

- Keep root `conftest.py` lean — only truly shared fixtures.
- Move fixtures down to the most specific directory that uses them.
- Do not import from `conftest.py` — pytest handles discovery automatically.
- If a fixture is only used by one test file, define it in that file.

## pytest configuration

Configure pytest in `pyproject.toml` under `[tool.pytest.ini_options]`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
python_classes = ["Test*"]
addopts = "-q --strict-markers --strict-config"
markers = [
    "slow: marks tests as slow",
    "integration: marks integration tests",
    "unit: marks unit tests",
    "e2e: marks end-to-end tests",
]
filterwarnings = [
    "error",              # treat warnings as errors by default
    "ignore::DeprecationWarning:third_party_lib.*",
]
```

Key settings:

- `testpaths` — where pytest looks for tests. Speeds up collection.
- `strict_markers` — unregistered markers cause an error (catches typos).
- `strict_config` — invalid config keys cause an error.
- `addopts` — default CLI flags applied to every run.
- `filterwarnings` — treat warnings as errors to catch issues early.

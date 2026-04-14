# Python Testing

# applies-to: **/*.py, **/*.pyi

> This file extends [common/testing.md](../common/testing.md) with Python-specific content.

## Framework: pytest

Use **pytest** exclusively. Do not use `unittest.TestCase` for new tests.

## Mandatory pytest markers

Every test function and test class must have a pytest marker. Use module-level
`pytestmark` for files where all tests share the same marker.

### Module-level pattern (required in every test file)

```python
import pytest

pytestmark = pytest.mark.unit

def test_example():
    assert 1 + 1 == 2
```

### Marker decision table

| Situation | Marker |
|---|---|
| Pure logic, no I/O, mocked boundaries | `unit` |
| Touches filesystem, subprocess, or database | `integration` |
| Full application flow with external systems | `e2e` |
| Test that guards a specific fixed bug | `regression` |
| Test that consistently runs over 1 second | `slow` |
| Minimal health check or deploy verification | `smoke` |

### Available markers

Defined in `pyproject.toml` under `[tool.pytest.ini_options].markers`:
- `unit` — fast isolated tests, boundaries mocked
- `integration` — cross-module, real I/O, subprocesses
- `e2e` — full stack or external systems
- `regression` — guards a fixed bug
- `slow` — exceeds ~1s
- `smoke` — minimal deploy/health checks

### Enforcement

- `--strict-markers` is enabled — any unlisted marker causes a test failure.
- Unmarked tests will fail collection.
- Every new test file **must** set `pytestmark = pytest.mark.<marker>` at module level.
- To add a new marker, define it in `pyproject.toml` first.

## Directory layout

```
tests/
├── conftest.py          # global fixtures (db, config, factories, etc.)
├── test_imports.py
├── e2e/
│   └── test_*.py
├── integration/
│   └── test_*.py
└── unit/
    ├── test_*.py
    └── common/
        └── test_*.py    # tests for src/<pkg>/common/ modules
```

Test files are organised by test type into subdirectories:

- `tests/unit/` — fast isolated tests, boundaries mocked.
- `tests/integration/` — cross-module, real I/O, subprocesses.
- `tests/e2e/` — full application flow with external systems.

Source-to-test mapping:

```
src/<pkg>/core.py           → tests/unit/test_core.py
src/<pkg>/cli.py            → tests/unit/test_cli.py
src/<pkg>/common/utils.py   → tests/unit/common/test_utils.py
src/<pkg>/common/decorators.py → tests/unit/common/test_decorators.py
```

Files: `test_<module>.py`. Functions: start with `test_`.

## Running tests

```bash
just test           # pytest -q
just test-parallel  # pytest -q -n auto
just coverage       # pytest --cov=src --cov-report=term-missing
```

## Fixtures

Define shared fixtures in `conftest.py`. Use `tmp_path` for temporary files:

```python
import pytest
from mypackage.core import AppContext

@pytest.fixture()
def app_context() -> AppContext:
    ctx = AppContext()
    yield ctx
    ctx.close()
```

## Parametrised tests

```python
@pytest.mark.parametrize(("input_val", "expected"), [
    ("hello world", "hello-world"),
    ("UPPER", "upper"),
])
def test_slugify(input_val: str, expected: str) -> None:
    assert slugify(input_val) == expected
```

## Mocking

Mock at the boundary — mock I/O calls, not internal helpers:

```python
def test_fetch_user_returns_none_when_not_found(mocker):
    mocker.patch("mypackage.db.execute", return_value=[])
    result = fetch_user(user_id=99)
    assert result is None
```

## Exception testing

```python
def test_raises_on_invalid_email():
    with pytest.raises(ValueError, match="invalid email"):
        validate_email("not-an-email")
```

## Coverage

- Overall threshold: ≥ 85 %.
- Coverage measured on `src/` only; test files excluded.
- Configuration in `pyproject.toml` under `[tool.coverage.*]`.

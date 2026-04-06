# Python Testing

# applies-to: **/*.py, **/*.pyi

> This file extends [common/testing.md](../common/testing.md) with Python-specific content.

## Framework: pytest

Use **pytest** exclusively. Do not use `unittest.TestCase` for new tests.

## Directory layout

```
tests/
├── conftest.py
├── test_core.py
└── <package>/
    └── test_module.py
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

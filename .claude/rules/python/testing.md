# Python Testing

# applies-to: **/*.py, **/*.pyi

> This file extends [common/testing.md](../common/testing.md) with Python-specific content.

## Framework: pytest

Use **pytest** exclusively. Do not use `unittest.TestCase` for new tests. Mixing styles
in the same file is not allowed.

## Directory layout

```
tests/
├── conftest.py          # shared fixtures
├── test_core.py         # tests for src/<package>/core.py
├── <package>/
│   ├── test_module_a.py
│   └── test_module_b.py
└── test_imports.py      # smoke test: every public symbol is importable
```

### Meta-repo (this template repository)

Generated projects follow the layout above. **This Copier meta-repository** has no `src/` tree;
Python under test lives in `scripts/`. Keep pytest modules organized as:

```
tests/
├── _paths.py            # REPO_ROOT, TEMPLATE_ROOT, COPIER_YAML (import from nested tests)
├── integration/
│   └── test_template.py # Copier copy/update integration suite
└── scripts/
    └── test_<script>.py # mirrors scripts/<script>.py
```

Do not flatten new tests into the top level of `tests/` unless they truly have no script or
integration home.

Files must be named `test_<module>.py`. Test functions must start with `test_`.

## Running tests

```bash
just test           # pytest -q
just test-parallel  # pytest -q -n auto (pytest-xdist)
just coverage       # pytest --cov=src --cov-report=term-missing
```

## Fixtures

Define shared fixtures in `conftest.py`. Use function scope unless a fixture is
explicitly expensive and safe to share:

```python
# conftest.py
import pytest
from mypackage.core import AppContext

@pytest.fixture()
def app_context() -> AppContext:
    ctx = AppContext()
    yield ctx
    ctx.close()
```

Use `tmp_path` (built-in pytest fixture) for temporary file operations. Never use
`/tmp` directly in tests.

## Parametrised tests

Use `@pytest.mark.parametrize` instead of looping inside a test function:

```python
@pytest.mark.parametrize(("input_val", "expected"), [
    ("hello world", "hello-world"),
    ("  leading", "leading"),
    ("UPPER", "upper"),
])
def test_slugify(input_val: str, expected: str) -> None:
    assert slugify(input_val) == expected
```

## Marks for categorisation

```python
@pytest.mark.unit
def test_pure_logic(): ...

@pytest.mark.integration
def test_reads_from_disk(): ...

@pytest.mark.slow
def test_full_pipeline(): ...
```

Run a subset: `uv run pytest -m unit`.

## Mocking

Use `unittest.mock` (or `pytest-mock`'s `mocker` fixture). Mock at the boundary —
mock the I/O call, not an internal helper:

```python
def test_fetch_user_returns_none_when_not_found(mocker):
    mocker.patch("mypackage.db.execute", return_value=[])
    result = fetch_user(user_id=99)
    assert result is None
```

Do not patch implementation details that are not part of the public interface.

## Coverage requirements

- Overall threshold: ≥ 80 % (≥ 85 % for generated projects).
- New modules introduced in a PR must meet the threshold.
- Coverage is measured on `src/` only; test files are excluded from the report.

Configuration lives in `pyproject.toml` under `[tool.coverage.*]`.

## What to assert

- Assert on **observable behaviour**, not implementation steps.
- Avoid asserting on log output or internal state unless that is the feature under test.
- Use `pytest.raises` for exception testing:

```python
def test_raises_on_invalid_email():
    with pytest.raises(ValueError, match="invalid email"):
        validate_email("not-an-email")
```

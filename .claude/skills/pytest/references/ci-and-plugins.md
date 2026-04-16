# CI, coverage, and plugins

This document covers integrating pytest with CI pipelines, enforcing coverage
thresholds, and useful plugins that enhance the testing workflow.

## Table of contents

- [Coverage with pytest-cov](#coverage-with-pytest-cov)
- [Coverage configuration](#coverage-configuration)
- [CI integration patterns](#ci-integration-patterns)
- [Useful pytest plugins](#useful-pytest-plugins)
- [Performance and parallelism](#performance-and-parallelism)
- [Strict mode](#strict-mode)

---

## Coverage with pytest-cov

`pytest-cov` adds coverage measurement to pytest runs. It wraps the `coverage.py`
library and integrates with pytest's collection and reporting.

### Running coverage

```bash
just coverage          # project recipe — runs pytest with coverage
pytest --cov=src --cov-report=term-missing
```

The `term-missing` report shows which lines are not covered:

```
Name                     Stmts   Miss  Cover   Missing
------------------------------------------------------
src/myapp/core.py           45      3    93%   67-69
src/myapp/auth/login.py     32      0   100%
```

### Coverage thresholds

Set a minimum coverage percentage to prevent regressions:

```toml
# pyproject.toml
[tool.coverage.report]
fail_under = 85
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.",
    "if TYPE_CHECKING:",
]
```

The `fail_under` setting makes the coverage report exit non-zero if coverage drops below
85%, which fails the CI check.

### What to exclude from coverage

Some code is not worth testing and should be excluded from the coverage report:

- `if __name__ == "__main__":` blocks.
- Type-checking imports (`if TYPE_CHECKING:`).
- Abstract method stubs.
- Platform-specific code that cannot run in CI.

Use `# pragma: no cover` sparingly and document why.

## Coverage configuration

```toml
# pyproject.toml
[tool.coverage.run]
source = ["src"]
branch = true               # measure branch coverage, not just line coverage

[tool.coverage.report]
fail_under = 85
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.",
    "if TYPE_CHECKING:",
    "@overload",
]

[tool.coverage.html]
directory = "htmlcov"        # output directory for HTML reports
```

**Branch coverage** (enabled with `branch = true`) checks whether both sides of every
`if` statement are exercised. It catches cases where line coverage is 100% but a branch
was never taken.

## CI integration patterns

### GitHub Actions example

```yaml
- name: Run tests with coverage
  run: |
    just coverage
  env:
    PYTHONPATH: src

- name: Upload coverage report
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: coverage-report
    path: htmlcov/
```

### Key CI practices

- Run the full test suite on every push and pull request.
- Use `--strict-markers` and `--strict-config` to catch configuration issues.
- Cache the virtual environment to speed up CI runs.
- Set `fail_under` in coverage config so drops fail the build.
- Use `pytest --tb=short` in CI for compact tracebacks.
- Use `pytest --junitxml=results.xml` to generate reports CI systems can parse.

### Fail fast vs full run

- **During development:** use `pytest -x` (stop on first failure) for fast feedback.
- **In CI:** run the full suite to catch all failures in one pass.
- **Compromise:** `pytest --maxfail=5` — stop after 5 failures to save time on
  catastrophic breaks.

## Useful pytest plugins

| Plugin                  | Purpose                                            |
|-------------------------|----------------------------------------------------|
| `pytest-cov`            | Coverage measurement and reporting                 |
| `pytest-mock`           | `mocker` fixture wrapping `unittest.mock`          |
| `pytest-xdist`          | Parallel test execution across CPU cores           |
| `pytest-randomly`       | Randomise test order to catch hidden dependencies  |
| `pytest-timeout`        | Kill tests that hang beyond a time limit           |
| `pytest-rerunfailures`  | Retry flaky tests (temporary mitigation)           |
| `pytest-sugar`          | Better terminal output with progress bar           |
| `pytest-benchmark`      | Measure and track performance of code              |
| `pytest-httpx`          | Mock `httpx` HTTP requests                         |
| `responses`             | Mock `requests` library HTTP calls                 |
| `freezegun`             | Freeze time for deterministic datetime testing     |
| `factory-boy`           | Generate test data with factories                  |
| `hypothesis`            | Property-based testing — generates edge-case inputs|
| `pyfakefs`              | Fake filesystem for testing file operations        |

### Plugin selection guidance

Start minimal. Add plugins only when you have a specific problem to solve.

- **Every project** should have: `pytest-cov`, `pytest-mock`.
- **If tests are slow:** add `pytest-xdist` for parallelism.
- **If tests are flaky:** add `pytest-randomly` to expose order dependencies, then
  `pytest-timeout` to catch hangs.
- **If you test HTTP:** add `responses` (for `requests`) or `pytest-httpx` (for `httpx`).
- **If you need test data:** add `factory-boy` for complex models.
- **For edge-case hunting:** add `hypothesis` for property-based testing.

## Performance and parallelism

### pytest-xdist

Run tests in parallel across CPU cores:

```bash
pytest -n auto          # use all available cores
pytest -n 4             # use exactly 4 workers
```

**Caveats:**

- Tests must be truly isolated — no shared files, databases, or global state.
- Fixtures with `session` scope are created once per worker, not once total.
- Output is interleaved — use `--dist loadscope` to group by module.
- Some fixtures (like database connections) need per-worker isolation.

### Speeding up tests without parallelism

- **Use narrower fixture scopes.** A `session`-scoped database fixture that creates and
  destroys a database is slow. Consider a `module`-scoped fixture with transaction
  rollback instead.
- **Use `pytest --lf`** to rerun only last-failed tests during development.
- **Use `pytest -k`** to run a subset matching a keyword.
- **Profile with `--durations=10`** to find the slowest tests and fixtures.
- **Use `monkeypatch` instead of real I/O** where possible.
- **Mark and skip slow tests** during development — see below.

### Automated slow-test detection

The skill bundles scripts to automate slow-test management. Use them when
`--durations` reveals tests that consistently take over a second.

**Find slow tests:**

```bash
python <skill-path>/scripts/find_slow_tests.py --threshold 1.0
```

**Mark them automatically:**

```bash
python <skill-path>/scripts/find_slow_tests.py --threshold 1.0 \
  | python <skill-path>/scripts/mark_slow_tests.py
```

This adds `@pytest.mark.slow` to each slow function and ensures `import pytest` is
present. Use `--dry-run` on the marker script to preview changes first.

**Split fast and slow runs in CI:**

```yaml
# GitHub Actions — two parallel jobs
jobs:
  fast-tests:
    runs-on: ubuntu-latest
    steps:
      - run: pytest -m "not slow" -q
  slow-tests:
    runs-on: ubuntu-latest
    steps:
      - run: pytest -m "slow" -q
```

This keeps the fast feedback loop short while still running the full suite.

## Strict mode

Enable strict settings to catch configuration mistakes early:

```toml
[tool.pytest.ini_options]
addopts = "--strict-markers --strict-config"
```

- `strict_markers`: unregistered markers cause an error. Catches typos like
  `@pytest.mark.integation`.
- `strict_config`: unknown configuration keys cause an error. Catches stale or
  misspelled settings.

Also consider treating warnings as errors:

```toml
filterwarnings = [
    "error",
    "ignore::DeprecationWarning:some_third_party.*",
]
```

This ensures deprecation warnings are fixed promptly rather than accumulating silently.

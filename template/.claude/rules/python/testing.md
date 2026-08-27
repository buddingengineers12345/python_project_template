---
paths:
  - "**/*.py"
  - "**/*.pyi"
---

# Python Testing

- Use **pytest** exclusively; never `unittest.TestCase` for new tests.
- Every test file must set `pytestmark = pytest.mark.<marker>` at module level - `--strict-markers` is enabled; unmarked tests fail collection.
- Valid markers: `unit`, `integration`, `e2e`, `regression`, `slow`, `smoke` (defined in `pyproject.toml`). Default to `unit`; `integration`, `e2e`, `slow` opt-in via `--slow` or `--all` flags.
- Test layout: `tests/{unit,integration,e2e}/test_<module>.py` mirroring `src/<pkg>/<module>.py`.
- Coverage threshold: ≥ 85% on `src/`; run `just coverage` to verify. Use fixtures over shared mutable fixtures; factory functions preferred.
- Regression tests must fail before the fix is applied; verify the failure first, then apply the fix.
- Suppression comments on tests carry the rule code and reason (e.g., `# noqa: E501 line length unavoidable for this fixture`).

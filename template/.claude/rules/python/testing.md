---
paths:
  - "**/*.py"
  - "**/*.pyi"
---

# Python Testing

- Use **pytest** exclusively; never `unittest.TestCase` for new tests.
- Every test file must set `pytestmark = pytest.mark.<marker>` at module level — `--strict-markers` is enabled; unmarked tests fail collection.
- Valid markers: `unit`, `integration`, `e2e`, `regression`, `slow`, `smoke` (defined in `pyproject.toml`).
- Test layout: `tests/{unit,integration,e2e}/test_<module>.py` mirroring `src/<pkg>/<module>.py`.
- Coverage threshold: ≥ 85% on `src/`; run `just coverage` to verify.

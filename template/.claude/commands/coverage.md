---
description: Analyse test coverage and write tests to fill any gaps below the 85% threshold. Use when the user asks to "check coverage", "improve coverage", or "find uncovered code".
allowed-tools: Read Write Edit Grep Glob Bash(just *) Bash(uv *)
disable-model-invocation: true
---

Analyse test coverage and write tests for any gaps found.

## Steps

1. **Run coverage** — execute `just coverage` to get the full report with missing lines:
   ```
   uv run --active pytest tests/ --cov=my_library --cov-report=term-missing
   ```

2. **Parse results** — from the output identify:
   - Overall coverage percentage (target: ≥ **85 %** per `[tool.coverage.report] fail_under`)
   - Every module below 85 % (list module name + actual percentage + missing line ranges)

3. **Gap analysis** — for each under-covered module:
   - Open the source file at `src/my_library/`
   - Read the lines flagged as uncovered
   - Identify what scenarios, branches, or edge cases those lines represent

4. **Write missing tests** — for each gap:
   - Locate the appropriate test file under `tests/`
   - Write one or more test functions that exercise the uncovered lines
   - Follow the existing test style (arrange / act / assert, parametrize over similar cases)
   - Ensure new tests pass: run `just test` after writing them

5. **Re-run coverage** — run `just coverage` again and confirm overall coverage has improved
   and no module is below the 85 % threshold.

## Report format

```
## Coverage Report — my_library

Overall: X%  (target: ≥ 85%)

### Modules below threshold
| Module        | Coverage | Missing lines        |
|---------------|----------|----------------------|
| my_library.core | 72% | 45-52, 78 |

### Tests written
- tests/.../test_core.py: added test_edge_case_x, test_branch_y

### After fixes
Overall: Y%
```

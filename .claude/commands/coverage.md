Analyse test coverage and write tests for any gaps found.

## Steps

1. **Run coverage** — execute `just coverage` to get the full report with missing lines:
   ```
   uv run --active pytest --cov --cov-report=term-missing --cov-report=xml
   ```

2. **Parse results** — from the output identify:
   - Overall coverage percentage
   - Every module below **80 %** (list module name + actual percentage + missing line ranges)

3. **Gap analysis** — for each under-covered module:
   - Open the source file
   - Read the lines flagged as uncovered
   - Identify what scenarios, branches, or edge cases those lines represent

4. **Write missing tests** — for each gap:
   - Locate the appropriate test file in `tests/`
   - Write one or more test functions that exercise the uncovered lines
   - Follow the existing test style (arrange / act / assert, parametrize over similar cases)
   - Ensure new tests pass: run `just test` after writing them

5. **Re-run coverage** — run `just coverage` again and confirm overall coverage has improved.

## Report format

```
## Coverage Report

Overall: X%  (target: ≥ 80%)

### Modules below threshold
| Module        | Coverage | Missing lines        |
|---------------|----------|----------------------|
| foo.bar       | 62%      | 45-52, 78, 91-95     |

### Tests written
- tests/foo/test_bar.py: added test_edge_case_x, test_branch_y

### After fixes
Overall: Y%
```

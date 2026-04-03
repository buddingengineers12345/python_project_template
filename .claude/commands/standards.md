Run the complete standards enforcement suite and produce a consolidated report.

This is the "am I ready to merge?" command. It runs all checks and aggregates results.

## Checks to run (execute concurrently where possible)

1. **Static analysis** — `just lint` + `just type`
   - ruff: all configured rules (E, F, I, UP, B, SIM, C4, RUF, D, C90, PERF)
   - basedpyright: strict type checking

2. **Docstring coverage** — `just docs-check`
   - All public symbols have Google-style docstrings
   - All modules have module-level docstrings

3. **Test coverage** — `just coverage`
   - Report overall percentage and flag any module below 80 %

4. **Copier template integrity** (if any `.jinja` files are present)
   - Confirm no unresolved Copier conflict markers (`<<<<<<`, `>>>>>>`)
   - Confirm no stray `.rej` sidecar files

5. **Definition-of-done checklist** — for every function or class added/modified:
   - [ ] Code passes lint + type check
   - [ ] Google-style docstring present
   - [ ] All parameters and return type annotated
   - [ ] At least one test case exists
   - [ ] No `TODO`/`FIXME` left in modified code

## Output format

```
## Standards Report — <YYYY-MM-DD>

### ✓/✗ Static Analysis (ruff + basedpyright)
[errors or "All clean"]

### ✓/✗ Docstring Coverage
[violations or "All public symbols documented"]

### ✓/✗ Test Coverage
[modules below 80% or "All modules ≥ 80%"]
Overall: X%

### ✓/✗ Template Integrity
[issues or "No conflicts or .rej files"]

### Definition-of-Done Status
[any unchecked items or "All items complete"]

---
[✓ All standards checks passed — ready to merge.]
[OR]
[✗ N issue(s) must be resolved before merging. See action items above.]
```

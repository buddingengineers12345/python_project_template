Audit and repair documentation across all Python source files.

## Steps

1. **Run ruff docstring check** — `uv run --active ruff check --select D src/ tests/ scripts/`
   Report every violation with file, line, and rule code.

2. **Deep symbol scan** — for every `.py` file under `src/my_library/`, `tests/`, and `scripts/`:
   - Read the file
   - Identify all public symbols: module-level functions, classes, methods not prefixed with `_`
   - For each symbol check:
     a. **Exists** — a docstring is present
     b. **Summary** — first line is a single imperative sentence, under 79 chars, no trailing period
     c. **Args section** — present when the function has parameters (excluding `self`/`cls`)
        - Each parameter listed with its type (if not obvious from annotation) and description
        - Names match the actual parameter names exactly
     d. **Returns section** — present when the return type is not `None`
     e. **Raises section** — present when the function raises documented exceptions
     f. **Style** — Google convention (`Args:`, `Returns:`, `Raises:` section headers)

3. **Module docstrings** — verify each `.py` file has a module-level docstring that describes
   the module's purpose in one sentence.

4. **Fix all violations** — for each missing or malformed docstring, write a correct Google-style
   docstring. Base the content on the function's signature, body, and surrounding context.
   Do not invent descriptions — if the purpose is unclear, write a minimal stub with a `TODO`.

5. **Verify** — re-run `uv run --active ruff check --select D src/ tests/ scripts/` and confirm zero violations.

## Output format

```
## Documentation Audit — my_library

### Ruff violations: N found
[list violations]

### Symbol scan
Total public symbols: N
  Compliant: N
  Missing docstring: N  → fixed
  Malformed docstring: N  → fixed

### After fixes
Ruff D violations: 0
All public symbols documented: ✓
```

# Skill fallbacks

Use this file when a referenced skill is not installed. It provides inline guidance to substitute for each missing skill.

---

## `pytest` skill not available

Apply these defaults:
- Use plain `pytest` style (functions, not classes) unless the project already uses unittest.
- Name tests `test_<behaviour>_when_<condition>`.
- Read `references/test-patterns.md` in this skill for common patterns (fixtures, parametrize, async, coverage).
- Inspect `conftest.py` if it exists to understand available fixtures.

---

## `python-code-reviewer` skill not available

Apply this inline review checklist to changed files:

**Correctness**
- [ ] Does the implementation handle all acceptance criteria?
- [ ] Are edge cases (empty input, None, zero, negative) handled or explicitly out of scope?
- [ ] Are exceptions raised with meaningful messages?

**Clarity**
- [ ] Are names (variables, functions, classes) self-describing?
- [ ] Is there any dead code or commented-out block that should be removed?
- [ ] Are magic numbers extracted to named constants?

**Structure**
- [ ] Does each function do one thing?
- [ ] Is there any duplication that could be extracted?
- [ ] Are imports clean (no unused imports)?

**Type safety**
- [ ] Do all public functions have type annotations?
- [ ] Does `mypy --strict` (or equivalent) pass on changed files?

---

## `python-docstrings` skill not available

Apply this inline docstring policy:

```python
def function_name(param: Type) -> ReturnType:
    """One-line summary ending with a period.

    Extended description if the behaviour isn't obvious from the summary.
    Omit if the one-liner is sufficient.

    Args:
        param: Description (omit type — it's in the annotation).

    Returns:
        Description of the return value.

    Raises:
        ValueError: When param is out of range.
    """
```

Rules:
- Every public function, class, and method gets a docstring.
- Private functions (`_name`) get a docstring only if non-obvious.
- Use Google style (Args / Returns / Raises sections).
- First line is imperative mood: "Return the sum", not "Returns the sum".

---

## `ci-fixer` skill not available

When `just ci` (or equivalent) fails:

1. Read the full failure output. Categorise the failure:
   - **Test failure** → go back to GREEN stage with the failing test.
   - **Lint failure** (ruff, flake8) → fix each reported line; re-run linter only.
   - **Type error** (mypy) → add/fix annotations; re-run mypy only.
   - **Import error** → check for missing `__init__.py`, wrong module path, or missing dependency.
   - **Coverage below threshold** → write the missing test(s), return to RED.
2. Fix only the reported category. Do not make unrelated changes.
3. Re-run the full CI after fixing each category.
4. If stuck after two attempts, present the exact error to the user and ask for direction.

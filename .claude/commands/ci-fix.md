Diagnose and fix all CI failures in this project. You are an autonomous CI-fixing agent.

## Step 1 — Run CI and capture output

```bash
just ci 2>&1
```

If CI passes (exit 0), report success and stop.

## Step 2 — Classify failures

Parse the output and classify each failure into one of these categories:

| Category | Tool | Typical pattern | Fix strategy |
|---|---|---|---|
| **Format** | ruff format | "would reformat" | Run `just fmt` — fully automatic |
| **Lint** | ruff check | `E`, `F`, `I`, `UP`, `B`, `SIM`, `C4`, `RUF`, `PERF`, `T20` | Run `just fix` for auto-fixable; manual fix for others |
| **Docstring** | ruff `D` rules | `D1xx`, `D2xx`, `D3xx`, `D4xx` | Add or fix Google-style docstrings |
| **Type** | basedpyright | "error: Type X cannot be assigned to Y" | Fix type annotations, add casts, narrow types |
| **Test** | pytest | "FAILED tests/..." | Fix test or implementation logic |
| **Coverage** | pytest-cov | "FAIL Required test coverage" | Add missing tests |
| **Import** | ruff `I` rules | `I001` | Run `just fix` — auto-fixable |

## Step 3 — Fix in priority order

Fix failures in this order (cheapest and most impactful first):

1. **Format + Import** — `just fix && just fmt` (fully automatic)
2. **Lint** — `just fix` for auto-fixable, then manual fixes
3. **Docstrings** — add missing Google-style docstrings. Read the `python-docstrings`
   skill (`skills/python-docstrings/SKILL.md`) for guidance if available.
4. **Type errors** — fix annotations. Read the `python-code-quality` skill
   (`skills/python-code-quality/SKILL.md`) for basedpyright guidance if available.
5. **Test failures** — read the failing test, understand what it asserts, fix the
   implementation or the test. Read the `pytest` skill (`skills/pytest/SKILL.md`)
   for patterns if available.
6. **Coverage** — identify uncovered lines with `just coverage`, write tests.

## Step 4 — Iterate

After fixing each category:

1. Re-run `just ci 2>&1`
2. If new failures appear, classify and fix them
3. Repeat until CI passes (exit 0)

**Hard limit:** Do not attempt more than 5 full CI iterations. If still failing after 5
rounds, report the remaining failures and ask the user for guidance.

## Step 5 — Report

When CI passes (or after hitting the iteration limit), produce a summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CI Fix Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status:     ✅ ALL GREEN (or ❌ FAILURES REMAIN)
Iterations: N
Duration:   ~Xm

Fixes applied:
- [Format] Reformatted 3 files
- [Lint] Fixed 5 ruff violations (2 auto, 3 manual)
- [Docstring] Added docstrings to 2 functions
- [Type] Fixed 1 type annotation in core.py
- [Test] Fixed assertion in test_core.py

Files changed:
- src/mypackage/core.py
- tests/test_core.py

Remaining issues: (if any)
- <description>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Rules

- Fix the root cause, not the symptom. A `# type: ignore` is not a fix.
- Do not weaken linter or type checker configuration.
- Do not delete or skip tests to make CI pass.
- Do not use `--no-verify` on any git command.
- Every fix must preserve existing test behaviour — run tests after each change.
- If a fix requires architectural changes beyond the scope of the failing code,
  stop and ask the user instead of making sweeping changes.

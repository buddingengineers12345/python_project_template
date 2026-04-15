# Output format templates

> Always load this file in Phase 3. Choose the template that matches the review scope.
> Templates are shown as live Markdown — copy and fill in the placeholders.

---

## Verdict Decision Guide (read before selecting template)

| Situation | Verdict |
|-----------|---------|
| No CRITICAL or HIGH issues | **APPROVE** |
| 1–2 HIGH issues, no CRITICAL | **REQUEST CHANGES** |
| Any CRITICAL issue | **BLOCK** |
| New logic has no tests and project requires them | **REQUEST CHANGES** |
| Only LOW / nit issues remain | **APPROVE** (list nits as optional) |
| Hotfix under time pressure, 1 known HIGH issue | **APPROVE** + open follow-up ticket |

---

## Template A — Snippet / Function / Module Review

Use for: a pasted function, a single file, or a module-level review.

---

## Python Code Review

**Mode**: Quick / Standard / Deep
**Python version**: 3.11
**Tools run**: mypy, ruff, black, bandit, pytest — OR — Manual review only (tools not available)

> *Assumptions (fill in if context was absent):*
> e.g. "Treating this as a utility module, not a web handler."

---

### Summary

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | N | Block |
| HIGH | N | Warn |
| MEDIUM | N | Info |
| LOW | N | Nit |

**Verdict**: APPROVE / REQUEST CHANGES / BLOCK

---

### Findings

#### [CRITICAL] Title of the issue

**Location**: `path/to/file.py:42`
**Issue**: Clear description of the problem and why it matters (what can go wrong).

**Before:**

    # The problematic code
    eval(user_input)

**After:**

    # The corrected code
    import ast
    ast.literal_eval(user_input)

---

#### [HIGH] Title

**Location**: `path/to/file.py:17`
**Issue**: Description.

**Fix**: Description of change, plus a snippet if helpful.

    # corrected snippet here

---

#### [MEDIUM] Title

**Location**: `path/to/file.py:88`
**Issue**: Description.

**Fix**: Description or snippet.

---

#### [Nit] Title

**Location**: `path/to/file.py:5`
**Note**: Optional — not required to fix. e.g. "Could rename `d` to `user_data` for clarity."

---

### What's Working Well

- **[Specific pattern]**: Brief specific praise. Name the exact decision done well.
- **[Another item]**: ...

---

### Automated Tool Results

| Tool | Status | Notes |
|------|--------|-------|
| `mypy --strict` | Pass / Fail / Not run | ... |
| `ruff check` | Pass / Fail / Not run | ... |
| `black --check` | Pass / Fail / Not run | ... |
| `bandit -r -ll` | Pass / Fail / Not run | ... |
| `pytest --cov` | Pass / Fail / Not run | ... |

---

## Template B — PR / Diff Review

Use for: a GitHub/GitLab PR, a git diff, or a branch comparison.

---

## PR Review: #NUMBER — TITLE

**Reviewed**: DATE
**Author**: AUTHOR
**Branch**: `head-branch` → `base-branch`
**Scope**: +N / -N lines across N files
**Tools run**: mypy, ruff, black, bandit, pytest — OR — Manual only

---

### Decision: APPROVE / REQUEST CHANGES / BLOCK

**Summary**: One sentence verdict.
e.g. "Two HIGH issues in error handling should be resolved before merge."

---

### Summary Table

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 0 | Pass |
| HIGH | 2 | Warn |
| MEDIUM | 3 | Info |
| LOW | 1 | Nit |

---

### Findings

(Use the same finding format as Template A — Location / Issue / Before+After)

---

### Validation Results

| Check | Result | Notes |
|-------|--------|-------|
| `mypy --strict` | Pass / Fail / Skipped | ... |
| `ruff check` | Pass / Fail / Skipped | ... |
| `black --check` | Pass / Fail / Skipped | ... |
| `bandit -r -ll` | Pass / Fail / Skipped | ... |
| Tests | Pass / Fail / Skipped | coverage: N% |

---

### Files Reviewed

| File | Change | Notes |
|------|--------|-------|
| `src/auth.py` | Modified | Main logic change |
| `tests/test_auth.py` | Added | New tests |
| `requirements.txt` | Modified | New dep added |

---

### What's Working Well

...

---

### Discussion Points (optional)

Design observations that do not block merge but are worth discussing async:

- ...

---

## Template C — Module / Codebase Audit

Use for: Deep mode reviews of an entire module or unfamiliar codebase.

---

## Python Module Audit: `module_name`

**Date**: DATE
**Scope**: N files, ~N lines of code
**Python version**: 3.11
**Purpose**: What this module does

---

### Executive Summary

2–3 sentences: overall health, most critical areas, and the top recommendation.

---

### Risk Matrix

| Category | Risk | Key Issues |
|----------|------|------------|
| Security | High / Medium / Low | ... |
| Correctness | ... | ... |
| Test Coverage | ... | ... |
| Type Safety | ... | ... |
| Documentation | ... | ... |
| Performance | ... | ... |

---

### Critical Findings (must fix immediately)

...

### High Priority

...

### Recommended Improvements (medium / low — prioritised)

1. ...
2. ...

---

### Strengths

...

### Suggested Next Steps

1. Run `bandit -r . -ll` and address all HIGH findings
2. Enable `mypy --strict` incrementally, module by module
3. ...

---

## Tone Guidelines

**Use:**
- "This could be simplified by..."
- "Consider using X here — it makes the intent clearer."
- "Nice use of dataclasses for the config object — exactly the right pattern."
- "[Nit] Could rename `d` to `user_data` for clarity."
- "Would it make sense to extract this into a helper to separate concerns?"

**Avoid:**
- "This is wrong / bad / amateur."
- "You should know not to do this."
- "Obviously this needs to be..."
- Any language that judges the author rather than the code.

**For optional suggestions**: prefix with `[Nit]` or `[Suggestion]`.
**For design questions**: phrase as open questions, not commands.

---
name: tdd-workflow
description: >-
  Guide a complete Test-Driven Development (TDD) cycle for Python: discover the
  project, write a failing test (RED), write minimal implementation (GREEN),
  refactor both production and test code (REFACTOR), then validate with CI
  (VALIDATE). Always use this skill when the user says "implement with TDD",
  "test-driven development", "RED GREEN REFACTOR", "write tests first", "TDD
  workflow", "implement feature with tests", "write the test before the code",
  "fix this bug TDD-style", or any request to build or fix Python code following
  test-first discipline. This skill orchestrates pytest, python-code-reviewer,
  python-docstrings, and ci-fixer at the appropriate stage; it loads fallback
  guidance from references/skill-fallbacks.md when those skills are not
  installed.
---

# TDD Workflow Skill

This skill guides you and the user through a strict **RED → GREEN → REFACTOR → VALIDATE** cycle. The user makes decisions at every stage — what to test, how to implement, what to refactor. Your role is to keep the cycle honest, prompt the right actions, and call in specialist skills (or their fallbacks) at the right moment.

**Hard rules — never break these:**
- No implementation code before a failing test exists.
- No moving to REFACTOR before GREEN is confirmed.
- No declaring a cycle complete without the CI command exiting 0.
- No patching bugs without first writing a reproducing test.

---

## Stage Banner

Display this banner at the top of every response. Use `✓` for completed stages, `●` for the current one, `○` for upcoming.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TDD  ○DISCOVER  ○RED  ○GREEN  ○REFACTOR  ○VALIDATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Example mid-cycle (GREEN active, DISCOVER + RED done):
```
TDD  ✓DISCOVER  ✓RED  ●GREEN  ○REFACTOR  ○VALIDATE
```

---

## Stage 0 — DISCOVER: Understand the Project and Requirement

**Goal:** Know the codebase and express the requirement as testable behaviour before writing a single line.

### 0a. Detect commands

Read `references/ci-detection.md` and detect the project's test and CI commands. State them explicitly:
> "I'll use `pytest` for tests and `just ci` for full CI."

Let the user confirm or override.

### 0b. Explore the project

Scan these files and note what you find:
- `pyproject.toml` / `setup.cfg` — dependencies, tool config (pytest, mypy, ruff, coverage thresholds)
- `conftest.py` (root and any sub-packages) — available fixtures
- Existing test files matching the feature area — conventions in use (naming, parametrize, fixtures)
- The module(s) that will change — existing public API, type hints, docstring style

### 0c. Clarify the requirement

Ask the user to describe **behaviour**, not implementation. A good requirement can be expressed as "given X when Y then Z". Keep asking until you can write down acceptance criteria as observable outcomes — things a test could assert.

Output:
1. **Requirement summary** (one paragraph)
2. **Acceptance criteria** (numbered list of observable behaviours)
3. **Files that will change** (test file + implementation file)

Get explicit user approval before proceeding.

---

## Stage 1 — RED: Write a Failing Test

**Goal:** One test that asserts a single acceptance criterion and currently fails for the right reason.

### Steps

1. Load the `pytest` skill (read its `SKILL.md`) for project conventions. If unavailable, load `references/skill-fallbacks.md` → "pytest skill not available".
2. Also load `references/test-patterns.md` if you need a specific pattern (parametrize, async, fixtures, etc.).
3. Draft the smallest test capturing *one* acceptance criterion. Name it `test_<behaviour>_when_<condition>`. Use `assert` statements, not unittest methods. Avoid mocking unless I/O is involved.
4. Show the draft to the user and wait for approval or edits.
5. Write the approved test.
6. Run the test command.
7. **Classify the failure.** Only proceed if the failure is for the right reason:

   | Failure type | Meaning | Action |
   |---|---|---|
   | `AssertionError` | Function exists, wrong behaviour | ✅ Ideal RED |
   | `AttributeError` / `ImportError` | Module or function doesn't exist yet | ✅ Good RED |
   | `SyntaxError` / `IndentationError` | Test itself is broken | ❌ Fix test first |
   | `TypeError` (wrong signature) | Signature mismatch in test | ❌ Fix test first |
   | Unrelated exception from existing code | Regression in test suite | ❌ Investigate before continuing |

8. Show the failure output. State: *"RED confirmed — failing for the right reason."*

Do not proceed until RED is confirmed.

### Optional: commit the failing test

Some teams commit failing tests to make the intention explicit:
```bash
git add <test-file>
git commit -m "test: add failing test for <behaviour>"
```
Mention this to the user and follow their preference.

---

## Stage 2 — GREEN: Write Minimal Implementation

**Goal:** Make the failing test pass with the least code necessary. All other tests stay green.

### Steps

1. Implement *just enough* to pass the test. Favour clarity over cleverness.

   **Triangulation** — if the simplest passing implementation would be a hardcoded return value, that's legitimate. Write it. Then ask the user to write a second test that forces a real implementation. This technique — faking it until a second test demands more — is a core TDD move, not a shortcut.

2. Include type annotations on all public functions:
   ```python
   def process(value: int) -> str:
       ...
   ```

3. Show the draft. Wait for approval or edits.
4. Write the approved implementation.
5. Run the test command.
6. **Confirm all tests pass** — not just the new one. If anything regresses, fix it before continuing.
7. Check coverage on the new module:
   ```bash
   python -m pytest --cov=<module> --cov-report=term-missing
   ```
   New code should be fully covered. If not, surface the gap to the user — a test is probably missing.
8. State: *"GREEN confirmed — all tests pass."*

Do not proceed until GREEN is confirmed.

### Optional: commit GREEN

```bash
git add <implementation-file> <test-file>
git commit -m "feat: implement <behaviour>"
```

---

## Stage 3 — REFACTOR: Clean Up Code *and* Tests

**Goal:** Improve the design without changing behaviour. Tests remain green throughout every change.

### 3a. Review production code

1. Load the `python-code-reviewer` skill. If unavailable, use `references/skill-fallbacks.md` → "python-code-reviewer skill not available".
2. Load the `python-docstrings` skill. If unavailable, use `references/skill-fallbacks.md` → "python-docstrings skill not available".
3. Collect their feedback. Group suggestions:
   - **Naming & clarity** — variable names, function signatures, magic numbers
   - **Structure** — duplication, abstraction opportunities, single-responsibility violations
   - **Docstrings** — missing or inadequate
   - **Style** — PEP 8, type hints, unused imports

### 3b. Review test code

Tests are first-class code. Review them separately:
- Can repetitive test functions be replaced with `@pytest.mark.parametrize`?
- Are fixtures the right tool for shared setup?
- Do test names read like specifications?
- Does any test assert more than one behaviour? (Split it.)
- Is there shared mutable state across tests? (Extract to fixtures with appropriate scope.)

### 3c. Apply changes

Let the user choose which suggestions to act on. Apply one logical group at a time. After every group, run the test command. If tests go red, revert the last change immediately and investigate before continuing.

### 3d. Wrap up

State: *"REFACTOR complete — all tests still passing."*

### Optional: commit REFACTOR

```bash
git commit -am "refactor: <what was improved>"
```

---

## Stage 4 — VALIDATE: CI Gate

**Goal:** The full pipeline passes. Nothing is done until this exits 0.

### Steps

1. Run the CI command.
2. **If all green:** Summarise the cycle — acceptance criteria covered, files changed, tests added, notable design decisions.
3. **If anything fails:** Do not attempt ad-hoc fixes. Load the `ci-fixer` skill. If unavailable, use `references/skill-fallbacks.md` → "ci-fixer skill not available". Fix one failure category at a time, re-running CI after each.
4. Only declare the cycle complete when CI exits 0.

---

## Multi-Criterion Features

When the feature has several acceptance criteria:

1. Run the full **RED → GREEN** loop for *each* criterion in order.
2. Do not enter REFACTOR until all criteria have passing tests.
3. If two criteria share a fixture, extract it to `conftest.py` during the second RED pass — before writing the second test, not later during REFACTOR.

---

## Bug Fix Protocol

When fixing a bug rather than building a feature, the cycle starts at RED with a reproducing test:

1. Write a test that *reliably triggers the bug*. Run it. Confirm it fails (`AssertionError` on wrong output, or an unexpected exception being raised).
2. Do not touch production code yet.
3. Proceed from GREEN: fix the bug with the minimal change that makes the test pass.
4. Continue through REFACTOR and VALIDATE as normal.

Never patch first. A bug without a reproducing test will return.

---

## Efficiency: batch edits and parallel calls

- **Batch edits:** When writing the test file in RED or the implementation in
  GREEN, write the complete file content in a single Edit call rather than
  adding functions one by one.
- **Read before edit:** Read the target module and existing test file once before
  planning changes. Apply all edits in the fewest calls possible.
- **REFACTOR batching:** Group related refactoring changes (e.g., all naming
  fixes) into a single Edit call per file. Run tests after each logical group,
  not after each individual change.

## Skill dependencies

| Stage    | Load first                                          | Fallback (if not installed)     |
|----------|-----------------------------------------------------|---------------------------------|
| DISCOVER | `references/ci-detection.md`                        | *(self-contained)*              |
| RED      | `pytest` skill + `references/test-patterns.md`      | `references/skill-fallbacks.md` |
| GREEN    | *(none)*                                            | —                               |
| REFACTOR | `python-code-reviewer`, `python-docstrings` skills  | `references/skill-fallbacks.md` |
| VALIDATE | `ci-fixer` skill (on failure only)                  | `references/skill-fallbacks.md` |

Load each skill at the start of the stage that needs it, not all upfront.

## Quick reference: where to go deeper

| Topic | Reference file |
|---|---|
| CI and test command detection | [references/ci-detection.md](references/ci-detection.md) |
| Fallback guidance when skills are missing | [references/skill-fallbacks.md](references/skill-fallbacks.md) |
| pytest patterns and fixtures | [references/test-patterns.md](references/test-patterns.md) |

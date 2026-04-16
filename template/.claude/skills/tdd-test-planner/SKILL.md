---
name: tdd-test-planner
description: >-
  Convert a requirement, user story, feature description, or bug report into a
  structured pytest test plan — before writing any implementation code. Use
  this skill whenever someone asks: "plan my tests", "what tests should I
  write", "test cases for this feature", "break down requirements into tests",
  "generate test skeleton", "what edge cases should I cover", "help me TDD
  this", "write tests first", "TDD approach", "before I implement", "spec my
  tests", "what should I assert", or any request to systematically derive test
  cases from a requirement. Also trigger when a user pastes a ticket, spec,
  user story, or bug report and asks how to approach testing it. Produces
  categorised test cases (happy path, error path, boundary values, edge cases,
  integration points) plus pytest skeletons with AAA structure, fixtures,
  parametrize patterns, and markers — but no implementation bodies. Always use
  this skill when the user is planning tests before writing code.
---

# TDD Test Planner Skill

Converts a requirement into a structured test plan and pytest skeletons.
No implementation code is written — only test shapes the developer then fills in.

## Quick reference: where to go deeper

| Topic | Reference file |
|---|---|
| AAA scaffolding, parametrize, async, conftest layout | [references/pytest-patterns.md](references/pytest-patterns.md) |
| Stub, mock, fake, spy taxonomy and decision guide | [references/test-doubles.md](references/test-doubles.md) |

---

## Step 1 — Scope calibration

Before building the matrix, classify the subject under test. This determines
which categories are relevant.

| Subject type | Required categories |
|---|---|
| Pure function (no I/O, no side effects) | A, B, C, D |
| Stateful class / service (in-process only) | A, B, C, D + E (collaborators within process) |
| REST / GraphQL endpoint | A, B, C, D, E |
| CLI command | A, B, D, E |
| Background job / worker | A, B, D, E |
| Data pipeline / ETL | A, B, C, D, E |

Skip a category entirely if it genuinely doesn't apply — don't generate empty
sections. Add a brief note explaining the omission (e.g. `*(E omitted — pure
function, no external collaborators)*`).

---

## Step 2 — Parse the requirement

Extract:

- **Subject under test** — class / function / endpoint / module being built
- **Primary inputs** — argument types, payload shapes, caller context
- **Expected outcomes** — what success looks like
- **Stated constraints** — validations, limits, business rules explicitly mentioned
- **Implicit constraints** — obvious requirements not stated; mine these sources:
  - Required-field validation on any "create / update" operation
  - Idempotency: calling twice should equal calling once (for writes)
  - Ordering guarantees: does the caller depend on sorted / stable output?
  - Thread safety: shared state under concurrent access
  - Audit trail: events, logs, or side-effects the spec implies
  - Auth / authorisation on any protected resource
  - Backwards compatibility if the subject is an existing interface

If the requirement is vague, note ambiguities as `⚠ Assumption:` rather than
asking for clarification — the developer can verify at review time.

---

## Step 3 — Build the test matrix

#### A — Happy Path
Core contract works end-to-end under normal conditions.
- One test per distinct success scenario.
- Use realistic inputs, not placeholders like `"foo"` / `1`.

#### B — Error Paths
Code rejects or handles bad inputs / states gracefully.
Mine every: validation rule, auth failure, missing required field, IO/network
failure (if applicable), conflicting state.

#### C — Boundary Values
Edges of numeric ranges, string lengths, collection sizes, time windows.
Rule of thumb: for range `[lo, hi]`, test `lo−1`, `lo`, `lo+1`, `hi−1`, `hi`,
`hi+1` — only the meaningful ones.
**Distinction from D:** boundary values are about *quantitative limits* defined
by the spec. Edge cases (D) are *structurally unusual inputs* that are valid
but surprising.

#### D — Edge Cases
Valid but unusual inputs that could silently produce wrong results:
empty collections, empty strings, zero, unicode/special characters, duplicate
items, None where an object is expected, very large inputs, NaN/Infinity for
floats.

#### E — Integration Points
Interactions with external collaborators (DB, API, filesystem, message queue,
another module). One test per meaningful interaction. If the test plan requires mocks, stubs, or fakes, load `references/test-doubles.md` to choose the right test double (stub/mock/fake).

---

## Step 4 — Select pytest mechanics

**Fixtures:** Use for any setup shared across 2+ tests. Fixtures used across
multiple test files belong in `conftest.py` — not inline. If you need specific pytest patterns (parametrize, fixtures, markers), load `references/pytest-patterns.md` for conftest layout and other patterns.

**Parametrize:** Use when the same assertion logic applies to multiple
input/output pairs. Always add human-readable `ids=` so test output says
`test_boundary[exact_balance]` not `test_boundary[100.0-True]`.

**Mocking decision:**
- Module-level attribute or global → `monkeypatch.setattr`
- Method on an object → `pytest-mock` (`mocker.patch.object`)
- Third-party library call → `unittest.mock.patch` as decorator
- Complex external system → fake (in-memory implementation) — see
  `references/test-doubles.md`

**Markers to apply:**
- `@pytest.mark.unit` — pure-logic tests, no I/O
- `@pytest.mark.integration` — hits real or fake external systems
- `@pytest.mark.slow` — anything > ~1 s
- `@pytest.mark.regression` — reproduces a specific bug
- `@pytest.mark.xfail(reason="...")` — unspecified or known-broken behaviour

**Async:** if the subject is `async def`, skeletons use `async def test_...`
and `@pytest.mark.asyncio`. See `references/pytest-patterns.md` for async patterns.

**Property-based:** for C / D categories with large combinatorial input spaces,
consider adding a `hypothesis` `@given` test alongside the parametrized ones —
flag it with a `# Optional: property-based with hypothesis` comment.

Custom markers must be registered in `pytest.ini` / `pyproject.toml`. Include
this snippet in every plan that uses custom markers:

```ini
# pytest.ini  (or [tool.pytest.ini_options] in pyproject.toml)
[pytest]
markers =
    unit: pure-logic tests with no I/O
    integration: tests that hit external systems
    slow: tests that take more than ~1 second
    regression: tests that reproduce specific bugs
```

---

## Step 5 — Output format

Produce the plan in this exact structure:

---
**## Test Plan: \<Subject Under Test\>**

**### Requirement Summary**
2–4 sentence restatement.
`⚠ Assumption:` any ambiguity resolved with an assumption (omit if none).

**### pytest mechanics**
- File: `tests/unit/test_<module>.py` (or `tests/integration/`, `tests/e2e/` as appropriate)
- Fixtures: list; note which belong in `conftest.py`
- Parametrize groups: which test groups use parametrize
- Markers: unit / integration / regression / slow as applicable
- Mocking: what, which tool, why

**### Test Cases**

For each applicable category:

| # | Test name | Scenario | Expected |
|---|-----------|----------|----------|
| A1 | `test_...` | one-liner | one-liner |

*(omit any category that doesn't apply; note why inline)*

**### Skeletons**

conftest.py skeleton (only if shared fixtures exist), then `tests/unit/test_<module>.py`:

Every test function body uses Arrange / Act / Assert comments with `...` under each.
Every function ends with `# [A1]` (or matching ID) in the signature comment.

Example shape:

```python
@pytest.mark.unit
def test_example(some_fixture):  # [A1]
    """Scenario description → expected outcome."""
    # Arrange
    ...
    # Act
    ...
    # Assert
    ...
```

**### pytest.ini snippet**
Marker registration block (if custom markers are used).

**### Implementation Checklist**
One `- [ ]` entry per test case, in A→E order, referencing both the ID and
function name.

---

## Style rules for skeletons

- **No implementation bodies** — use `# Arrange / # Act / # Assert` comments
  with `...` under each, never bare `...` alone.
- **ID tags** — every skeleton function ends its first line with `# [A1]` etc.
  so it maps back to the table and checklist.
- **Descriptive names** — `test_create_user_with_duplicate_email_raises_conflict`
  not `test_error_case_2`.
- **Integration mocks** — add `# TODO: use <stub|mock|fake> for <collaborator>`
  directly above the test body.
- **Imports** — `import pytest` at top; `from <module> import <subject>` using
  the most obvious path derivable from the requirement.
- **Class grouping** — for a subject with 8+ tests, wrap in
  `class TestSubjectName:` — see `references/pytest-patterns.md`.

---

## Calibration notes

- **TDD-first mode** (writing tests before any code): generate only the tests
  needed to specify the *next* behaviour. Prefer fewer, focused tests that each
  drive one implementation decision.
- **Test-after mode** (adding tests to existing code): lean toward completeness.
  It is easier to delete a redundant test than to discover a gap in production.
- **Don't invent behaviour** — if the requirement is silent on a scenario, mark
  the test `@pytest.mark.xfail(reason="behaviour not yet specified")` and log
  a `⚠ Assumption`.
- **Test contracts, not internals** — assert public return values, raised
  exceptions, and observable side-effects. Never assert private attributes or
  call order unless the spec explicitly requires it.
- **Parametrize boundary values** — a single parametrized test with `ids=` is
  almost always cleaner than N near-identical named tests.

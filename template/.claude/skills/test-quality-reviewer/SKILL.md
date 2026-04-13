---
name: test-quality-reviewer
description: >-
  Review pytest test files for quality and trustworthiness. Use for "review my tests",
  "are my tests good?", "test quality check", "audit my test suite", or any request to
  evaluate existing test code. Checks naming, AAA structure, assertions, test isolation,
  parametrization, fixtures, async correctness, markers, imports, test doubles, and
  coverage alignment. Produces structured review with health score, severity-ranked issues,
  Quick Wins, and before/after fixes. Complements pytest-writing skills by focusing on
  quality assessment of existing tests — not just how to write tests, but whether they're
  actually trustworthy.
---

# Test Quality Reviewer Skill

You are auditing pytest test files for quality, correctness, and improvement opportunities. Your goal: produce a structured, actionable report that helps the author build a test suite they can actually trust.

## Quick reference: where to go deeper

| Topic | Reference file |
|---|---|
| Before/after code for all common issues | [references/examples.md](references/examples.md) |
| Async testing, test doubles, conftest, property-based testing | [references/advanced-patterns.md](references/advanced-patterns.md) |

---

## Pre-Flight: What to Collect

Before analyzing, gather all relevant files:

1. **Test files** — `test_*.py` or `*_test.py` (flag if naming convention is inconsistent)
2. **conftest.py** — read alongside tests; fixture scope and sharing patterns live here
3. **Source files** — if provided, use for coverage alignment; if absent, note the limitation
4. **Config** — `pytest.ini`, `pyproject.toml [tool.pytest.ini_options]`, `setup.cfg [tool:pytest]`; look for registered markers, `testpaths`, `asyncio_mode`

---

## Scan Checklist

Work through every test file in this exact order. Check each box mentally:

- [ ] File and function **naming conventions**
- [ ] **AAA structure** per test function
- [ ] **Assertion quality** (what and how is being asserted)
- [ ] **Test isolation** (shared state, external deps, ordering assumptions)
- [ ] **Parametrization opportunities** (duplicate test structures)
- [ ] **Fixture quality** (scope, teardown, placement, god fixtures)
- [ ] **Async correctness** (if `async def` tests exist)
- [ ] **Floating-point comparisons**
- [ ] **Test markers** (skip reasons, unregistered custom markers)
- [ ] **Import hygiene** (imports inside test functions, star imports)
- [ ] **Test doubles** (right tool? mocks vs stubs vs fakes)
- [ ] **Coverage alignment** vs source (if source provided)

---

## Quality Criteria

### 1. Naming

Test names are specifications. They should read as behavior sentences.

| ✅ Good | ❌ Bad |
|---|---|
| `test_withdraw_raises_when_balance_insufficient` | `test_withdraw_error` |
| `test_parse_date_returns_none_for_empty_string` | `test_parse_date_2` |
| `test_user_becomes_admin_after_role_promotion` | `test_user_thing` |
| Class: `TestWithdrawal` | Class: `TestBankStuff` |

**Flags:** generic suffixes (`_test1`, `_case2`, `_new`), names that only repeat the function name, file names not matching `test_*.py` / `*_test.py`.

---

### 2. AAA Structure (Arrange / Act / Assert)

```python
def test_discount_applied_for_vip_customer():
    # Arrange
    customer = Customer(tier="vip")
    cart = Cart(items=[Item(price=100)])
    # Act
    total = cart.calculate_total(customer)
    # Assert
    assert total == 80
```

**Flags:**
- No arrangement (magic values inlined into the call)
- Multiple Act phases in one test (two SUT calls — split into two tests)
- Assertions before the Act
- Test verifies X *and* Y *and* Z (multiple unrelated behaviors — each should be its own test)

---

### 3. Assertion Quality

| Issue | Bad | Fix |
|---|---|---|
| Bare truthiness on complex value | `assert result` | `assert result is not None` |
| `== True` / `== False` | `assert x == True` | `assert x` or `assert x is True` |
| `!= None` | `assert x != None` | `assert x is not None` |
| `len(x) > 0` | `assert len(result) > 0` | `assert result` |
| Compound assert | `assert a and b and c` | Three separate asserts |
| unittest-style in pytest | `self.assertEqual(a, b)` | `assert a == b` |
| Asserting repr/str | `assert str(user) == "Alice (admin)"` | `assert user.name == "Alice"` |
| Opaque computed values | `assert x == y` (both computed) | `assert x == y, f"got {x!r}, expected {y!r}"` |
| **Floating-point exact equality** | `assert 0.1 + 0.2 == 0.3` | `assert 0.1 + 0.2 == pytest.approx(0.3)` |

> Any `assert <float_expr> == <literal>` without `pytest.approx` is a latent flaky test. Always flag as 🟡 Warning.

---

### 4. Test Isolation

Tests must be fully independent. Any single test should pass when run in isolation with `pytest path::test_name`.

**Flags:**
- Module-level mutable variables written by tests
- Global or class-level state not reset per-test
- Tests that call other test functions
- Missing `monkeypatch` / `mock.patch` for: network calls, DB writes, filesystem, `datetime.now()`, `random`, environment variables
- Filesystem writes without `tmp_path`
- `time.sleep()` — use mocked time or proper async primitives
- Hard-coded absolute paths (`/home/user/data/...`) or credentials in test code

---

### 5. Parametrization Opportunities

3+ tests with identical structure differing only in values → strong recommendation to parametrize.
2 tests → suggest as "consider parametrizing."

```python
# ❌ Duplicate structure × 3
def test_is_palindrome_racecar(): assert is_palindrome("racecar")
def test_is_palindrome_level():   assert is_palindrome("level")
def test_is_palindrome_hello():   assert not is_palindrome("hello")

# ✅
@pytest.mark.parametrize("word,expected", [
    ("racecar", True), ("level", True), ("hello", False),
])
def test_is_palindrome(word, expected):
    assert is_palindrome(word) == expected
```

**Anti-pattern:** over-parametrizing fundamentally different scenarios (different error types, different code paths) — produces confusing failure messages. Each logical case may deserve its own test.

---

### 6. Fixture Quality

**Flags:**
- Repeated 3+ line setup across multiple tests → extract as fixture
- God fixtures (one fixture bootstraps everything) → split by concern
- **Missing scope on expensive fixtures:** a fixture that opens a DB connection or starts a service defaulting to `scope="function"` runs N times unnecessarily → `scope="session"` or `scope="module"`
- **Scope too broad for mutable state:** `scope="session"` fixture that mutates anything causes cross-test pollution
- `yield` fixture without cleanup when cleanup is needed (DB rows, temp files, env vars)
- `autouse=True` on non-universal fixtures — hides dependencies
- Fixture used across multiple files but defined in a test file → move to `conftest.py`
- Fixture only used in one file but lives in `conftest.py` → move to that file

**Scope quick guide:**

| Scope | Use when |
|---|---|
| `session` | Expensive, read-only (DB schema, server start) |
| `module` | Moderate cost, per-file shared state |
| `function` | Anything that mutates state (default) |

---

### 7. Async Testing

When `async def test_` functions are present:

**Flags:**
- Missing `@pytest.mark.asyncio` when `asyncio_mode` is not set to `"auto"` in config
- Using `asyncio.run()` inside a test function — this is the sync workaround, not the pytest-asyncio pattern
- `event_loop` fixture with `scope="session"` paired with `scope="function"` async fixtures — scope mismatch causes errors in pytest-asyncio ≥0.21
- `time.sleep()` in async tests instead of `await asyncio.sleep()`
- `pytest-asyncio` not in test dependencies

See `references/advanced-patterns.md → Async Testing` for examples.

---

### 8. Test Markers

**Flags:**
- `@pytest.mark.skip` without `reason="..."` — becomes permanent; no one knows why
- `@pytest.mark.xfail` without `reason` or `strict=True` — hides real failures silently
- Custom markers (`@pytest.mark.slow`, `@pytest.mark.integration`) not registered in config → `PytestUnknownMarkWarning`
- No marker strategy for separating slow/integration/external tests from the fast unit suite

**Good config pattern:**
```ini
# pytest.ini
[pytest]
markers =
    slow: marks tests as slow (deselect with -m "not slow")
    integration: requires external services
```

---

### 9. Import Hygiene

**Flags:**
- Imports inside test functions — slows startup, hides dependency structure, common in copy-pasted tests
- `from module import *` — impossible to know where names come from
- Importing from a different path than the installed package — may test a stale copy

---

### 10. Test Doubles

Using the wrong test double produces over-mocked, brittle tests.

| Double | Behavior | Assert on it? | Use when |
|---|---|---|---|
| **Stub** | Returns fixed values | No | Replacing external data sources |
| **Mock** | Records calls | Yes | Verifying side effects (emails, events) |
| **Spy** | Wraps real object, records calls | Yes | Need real behavior + call verification |
| **Fake** | Simplified real implementation | No | In-memory DB, fake filesystem |

**Flags:**
- `Mock` where a plain return value (stub) would be simpler
- `assert mock.called` — use `mock.assert_called_once_with(...)` to catch argument errors
- Mocking private methods of the SUT — couples tests to implementation details
- Mocks without `spec=` — typos in attribute/method names silently pass

See `references/advanced-patterns.md → Test Doubles` for examples.

---

## Anti-Pattern Catalogue

### 🔴 Critical

| Anti-pattern | Why it's critical |
|---|---|
| **Test interdependence** | Fails with `--randomly`, `-k`, or parallel CI; suite order should never matter |
| **Asserting nothing** | `def test_x(): do_thing()` — always green; proves nothing |
| **Silent exception swallow** | `try: thing() except: pass` — test can never fail |
| **Testing the mock, not the code** | `assert mock.called` — verifies wiring, not behavior |
| **Production state mutation** | Writes to real DB/FS/service without cleanup |
| **Float exact equality** | `assert result == 0.3` — flaky across environments |

### 🟡 Warning

| Anti-pattern | Note |
|---|---|
| **Magic numbers / strings** | `assert result == 42` — extract as named constant or add explanation |
| **`time.sleep()` in tests** | Non-deterministic; flakes under CI load |
| **Test logic (if/else)** | `if x: assert a else: assert b` → parametrize |
| **Over-mocking** | So many mocks the test only verifies the wiring |
| **Giant tests** | >30 lines is a smell; >50 lines — split |
| **`@pytest.mark.skip` without reason** | Becomes permanent tech debt |
| **Expensive fixture with wrong scope** | `scope="function"` on DB connection = N × overhead |
| **`yield` fixture without cleanup** | Leaves dirty state for later tests |
| **`assert mock.called`** | Hides wrong argument errors; use `assert_called_once_with()` |
| **Asserting repr/str** | Fragile; breaks when `__repr__` changes |
| **Imports inside test functions** | Move to top-level |

### 🔵 Suggestion

| Anti-pattern | Note |
|---|---|
| **Missing edge cases** | No test for None, empty, zero, max boundary, unicode |
| **No error-path tests** | Functions that raise have no `pytest.raises` test |
| **Unregistered custom markers** | Add to config `markers =` section |
| **Missing `spec=` on mocks** | Typos in names won't be caught |
| **`print()` left in tests** | Use `capfd`/`capsys` or logging |
| **Commented-out tests** | Delete or fix — dead code |
| **`unittest.TestCase` without benefit** | Plain functions are simpler in pytest |
| **conftest.py hoarding** | Fixtures used in only one file don't belong in conftest |

---

## Coverage Alignment

When source files are provided:

1. **Untested public functions/methods** — every `def` without a leading underscore should have ≥1 test
2. **Untested branches** — each `if`/`elif`/`else`, `try`/`except`, early `return`
3. **Untested error paths** — every `raise` in source should have a corresponding `pytest.raises` test
4. **Untested boundary conditions** — min/max, empty collections, zero, None
5. **Over-tested private internals** — `_method` tests are brittle; suggest testing via public API

**File naming:** `myapp/auth.py` → `tests/test_auth.py` (not `tests/auth_tests.py`). Flag mismatches.

---

## Output Format

````
## Test Quality Review: <filename(s)>

### Health Score: N/10
<One-sentence verdict>

### Summary
- X tests across Y files; conftest.py: [reviewed / not present / not provided]
- Z issues: A 🔴 critical · B 🟡 warnings · C 🔵 suggestions

---

### ⚡ Quick Wins
The 3 highest-impact changes to make right now:
1. **[Fix type]** — specific action on specific tests
2. ...
3. ...

---

### 🔴 Critical Issues

#### [CRITICAL] <Short title>
**Location:** `test_file.py::test_name` (line N)
**Problem:** <What is wrong and why it makes the suite untrustworthy>
**Fix:**
```python
# before
<bad code>

# after
<fixed code>
```

---

### 🟡 Warnings

[same per-issue structure; group identical patterns:
"This pattern appears in 6 tests. Example: test_foo.py::test_bar. Fix pattern:"]

---

### 🔵 Suggestions

[same structure]

---

### Parametrization Opportunities

**Group: <description>**
Tests: `test_a`, `test_b`, `test_c`
```python
# before / after snippet
```

---

### Coverage Gaps  *(only if source was provided)*

| Function / Branch | File:Line | Gap |
|---|---|---|
| `parse_date` — None input | utils.py:42 | No test for None argument |

---

### What's Working Well
2-4 genuine positives. Always include this section, even for a bad suite.
````

---

## Health score rubric

Start at 10. Deduct −2 per Critical (cap −6), −0.5 per Warning (cap −3), −0.25 per Suggestion (cap −1).

| Score | Label |
|---|---|
| 9–10 | Excellent — trustworthy, maintainable |
| 7–8 | Good — minor issues, safe to ship |
| 5–6 | Acceptable — real problems but suite is useful |
| 3–4 | Needs Work — critical issues; suite gives false confidence |
| 1–2 | Poor — largely decorative; major rewrite needed |

## Tone and calibration

- Direct and constructive — goal is better tests, not blame.
- **Small files (<10 tests):** be thorough, call out every issue.
- **Large files (50+ tests):** focus on patterns and group identical issues with one representative example.
- If the suite is genuinely good, say so — don't manufacture issues.
- Always lead with Critical issues. Quick Wins must be concrete and specific.

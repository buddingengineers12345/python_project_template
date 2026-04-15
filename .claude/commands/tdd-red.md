---
description: Validate the RED phase of a TDD cycle — confirm a specific test fails for the right reason before implementation. Use when the user asks to "check RED", "verify RED phase", or after writing a new failing test.
argument-hint: [test-file-or-name]
allowed-tools: Read Bash(just test:*) Bash(uv run pytest:*)
---

Validate the RED phase of a TDD cycle: confirm that a specific test FAILS for the right reason.

Run the test suite with `just test` (or the specific test file if the user provides one).

Then analyse the output:

1. **Identify the new/target test** — the user should tell you which test they expect to fail, or you should identify the most recently written test.

2. **Classify the failure** using this table:

   | Failure type | Meaning | Verdict |
   |---|---|---|
   | `AssertionError` | Function exists, wrong behaviour | ✅ Ideal RED — proceed to GREEN |
   | `AttributeError` / `ImportError` | Module or function doesn't exist yet | ✅ Good RED — proceed to GREEN |
   | `NameError` | Name not defined | ✅ Good RED — proceed to GREEN |
   | `SyntaxError` / `IndentationError` | Test itself is broken | ❌ Fix the test first |
   | `TypeError` (wrong signature) | Signature mismatch in test | ❌ Fix the test first |
   | Test passes unexpectedly | Implementation already exists or test is wrong | ❌ Review the test |
   | Unrelated test fails | Regression in existing code | ❌ Investigate before continuing |

3. **Report the result** in this format:

   ```
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   TDD RED Validation
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Test:     <test name>
   File:     <test file path>
   Status:   FAIL ✅ (or PASS ❌ or ERROR ❌)
   Type:     <failure type from table>
   Message:  <first line of error message>

   Verdict:  RED CONFIRMED — ready for GREEN
             (or: FIX NEEDED — <what to fix>)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```

4. If RED is confirmed, remind the user: "Now write the minimal implementation to make this test pass. No more, no less."

5. If RED is not confirmed, explain exactly what needs fixing before the TDD cycle can continue.

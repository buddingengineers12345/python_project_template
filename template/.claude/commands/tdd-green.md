Validate the GREEN phase of a TDD cycle: confirm that the previously-failing test now PASSES and no regressions were introduced.

Run the full test suite with `just test`.

Then analyse the output:

1. **Identify the target test** — the test that was RED in the previous phase.

2. **Check three conditions:**
   - The target test now PASSES
   - ALL other tests still pass (no regressions)
   - No new warnings or errors were introduced

3. **Report the result** in this format:

   ```
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   TDD GREEN Validation
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Target test:  <test name>
   Status:       PASS ✅ (or FAIL ❌)

   Full suite:   X passed, Y failed, Z skipped
   Regressions:  None (or: <list of newly failing tests>)

   Verdict:      GREEN CONFIRMED — ready for REFACTOR
                 (or: NOT GREEN — <what to fix>)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```

4. If GREEN is confirmed, also run a quick coverage check:
   ```bash
   uv run pytest --cov=src --cov-report=term-missing -q
   ```
   Report coverage on the module that was changed. Flag any uncovered lines.

5. If GREEN is confirmed, remind the user: "Now review and refactor. Tests must stay green throughout. Run `just test` after every change."

6. If GREEN is not confirmed:
   - If the target test still fails: the implementation is incomplete. Show the error.
   - If other tests regressed: the implementation broke existing behaviour. List the regressions.
   - Advise fixing without over-engineering — GREEN means minimal, not perfect.

7. Reset the refactor edit counter if it exists:
   ```bash
   echo "0" > .claude/.refactor-edit-count 2>/dev/null || true
   ```

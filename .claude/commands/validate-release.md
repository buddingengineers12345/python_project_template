Simulate a release by rendering and testing the template with all feature combinations.

This command validates that a release won't break existing or new users by testing the template
against all possible feature combinations before you tag and ship.

## Prerequisites

- Working tree must be clean (`git status`)
- All changes must be committed
- `just ci` must pass

## Steps

1. **Verify prerequisites**
   ```bash
   git status                      # must show "nothing to commit"
   just ci                         # must pass completely
   ```
   If CI fails, fix issues and re-run before proceeding.

2. **Extract template version** from `pyproject.toml`
   ```bash
   VERSION=$(grep "^version = " pyproject.toml | sed 's/.*"\([^"]*\)".*/\1/')
   echo "Testing release for version: $VERSION"
   ```

3. **Generate test projects** — Create 4 temporary projects covering all feature combinations:

   **a) Minimal config** (all optional features disabled)
   ```bash
   copier copy . /tmp/test-minimal --trust --defaults \
     --data include_docs=false \
     --data include_numpy=false \
     --data include_pandas_support=false
   cd /tmp/test-minimal && just ci && cd -
   ```

   **b) Full-featured config** (all optional features enabled)
   ```bash
   copier copy . /tmp/test-full --trust --defaults \
     --data include_docs=true \
     --data include_numpy=true \
     --data include_pandas_support=true
   cd /tmp/test-full && just ci && cd -
   ```

   **c) Docs only**
   ```bash
   copier copy . /tmp/test-docs --trust --defaults \
     --data include_docs=true \
     --data include_numpy=false \
     --data include_pandas_support=false
   cd /tmp/test-docs && just ci && cd -
   ```

   **d) Data science stack** (numpy + pandas, no docs)
   ```bash
   copier copy . /tmp/test-datascience --trust --defaults \
     --data include_docs=false \
     --data include_numpy=true \
     --data include_pandas_support=true
   cd /tmp/test-datascience && just ci && cd -
   ```

4. **Capture results** — for each test project, record:
   - Config used (feature combination)
   - Exit code of `just ci`
   - Any error messages (if failed)

5. **Clean up** temporary directories
   ```bash
   rm -rf /tmp/test-minimal /tmp/test-full /tmp/test-docs /tmp/test-datascience
   ```

6. **Report results** to the user

## Success Criteria

All four feature combinations must pass `just ci` completely. If any combination fails:
- ✗ **Do NOT release** — fix the underlying issue first
- Report which combination failed and why
- Suggest fixes (e.g., missing dependency, syntax error in template)

## Output Format

```
## Release Validation — v<VERSION>

Testing template against all feature combinations...

| Config | Status | Time | Error |
|--------|--------|------|-------|
| Minimal (no features) | ✓ PASS | 45s | — |
| Full featured | ✓ PASS | 52s | — |
| Docs only | ✓ PASS | 48s | — |
| Data science stack | ✓ PASS | 50s | — |

✓ All feature combinations passed.
Ready to release v<VERSION> with confidence.

Next step: Run `/release` to tag and push.
```

OR (if a test fails):

```
## Release Validation — v<VERSION>

Testing template against all feature combinations...

| Config | Status | Time | Error |
|--------|--------|------|-------|
| Minimal | ✓ PASS | 45s | — |
| Full featured | ✗ FAIL | 42s | pytest: missing test files |
| Docs only | ✓ PASS | 48s | — |
| Data science stack | ✓ PASS | 50s | — |

✗ One configuration failed. Fix the issue and re-run validation.

**Issue:** Full-featured config (`include_docs=true, include_numpy=true, include_pandas_support=true`) fails at pytest stage.
**Likely cause:** Test template not rendering correctly when all features enabled.
**Suggested fix:** Review `template/tests/test_core.py.jinja` conditional logic.
```

## Tips

- Keep temp directories if a test fails (for debugging)
- If uv.lock generation is slow, consider passing `--skip-tasks` to copier (after validation passes)
- This is a pre-release gate — run it before `/release` every time

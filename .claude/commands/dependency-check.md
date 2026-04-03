Validate that `uv.lock` is in sync with `pyproject.toml` and committed.

This command ensures dependencies are reproducible and locked, catching silent drift that
can cause issues in CI or when collaborators pull changes.

## Prerequisites

None — runs on the current state of the repo.

## Steps

1. **Check if uv.lock exists**
   ```bash
   test -f uv.lock && echo "uv.lock exists" || echo "ERROR: uv.lock not found"
   ```
   If missing, the repo is not using uv's lock mechanism. Warn the user.

2. **Verify uv.lock is committed to git**
   ```bash
   git ls-files uv.lock | grep -q uv.lock && echo "Committed" || echo "NOT COMMITTED"
   ```
   If not committed, warn: "uv.lock must be committed to ensure reproducible installs."

3. **Check for uncommitted changes to uv.lock**
   ```bash
   git diff uv.lock | wc -l
   ```
   If output > 0, warn: "uv.lock has uncommitted changes. Run `git add uv.lock && git commit` to sync."

4. **Verify all extras are locked**

   Read `pyproject.toml` and extract all extra names under `[project.optional-dependencies]`:
   ```
   dev, test, docs (if include_docs enabled)
   ```

   Then check that `uv.lock` contains entries for all extras. Verify by scanning lock file for:
   ```
   [project optional-dependencies]
   dev = [...]
   test = [...]
   docs = [...] (if applicable)
   ```

5. **Verify lock file age**
   ```bash
   LOCK_DATE=$(stat -f%Sm -t%Y-%m-%d uv.lock)  # macOS
   # OR (Linux)
   LOCK_DATE=$(date -r uv.lock +%Y-%m-%d)
   ```
   If lock is older than 30 days, suggest: "Consider running `just update` to refresh dependencies."

6. **Dry-run dependency sync** (optional, helps catch issues early)
   ```bash
   uv sync --frozen --extra dev --no-install
   ```
   If this fails, report the error. Common issues:
   - `pyproject.toml` has unpinned versions (should be allowed, but check for overconstraint)
   - Missing dependencies specified in extras

## Output Format

```
## Dependency Check

✓ uv.lock exists and is committed
✓ No uncommitted changes to uv.lock
✓ All extras locked: dev, test, docs
✓ Lock file is recent (2026-04-02)
✓ Dry-run sync successful

All dependency checks passed.
```

OR (with issues):

```
## Dependency Check

✓ uv.lock exists and is committed
✗ UNCOMMITTED CHANGES to uv.lock
  → Run: git add uv.lock && git commit -m "chore: refresh dependencies"
✓ All extras locked: dev, test
✗ Missing extra: docs (declared in pyproject.toml but not in lock)
  → Run: uv lock --upgrade && uv sync --frozen --extra docs
✗ Lock file is 42 days old
  → Consider refreshing: just update

Action items (before pushing):
1. Commit uv.lock changes
2. Lock the missing extras
3. Refresh dependencies to latest versions
```

## Tips

- Run this before every commit to catch dependency drift
- If `uv.lock` is gitignored (unusual but possible), you're not benefiting from reproducible installs
- Lock file age is advisory only; very old locks are fine if dependencies are stable
- Always commit `uv.lock` to the repository — this is a uv best practice

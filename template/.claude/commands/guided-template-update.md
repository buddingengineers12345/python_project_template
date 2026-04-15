---
description: Interactively update this project to the latest Copier template version, with conflict detection and CI verification. Use when the user asks to "update the template", "run a guided template update", or "sync with the template".
allowed-tools: Read Write Edit Grep Bash(git *) Bash(copier *) Bash(just ci:*) Bash(find *) Bash(test *) Bash(jq *)
disable-model-invocation: true
context: fork
---

Interactively update this project to the latest template version with full guidance.

This command makes template updates safe and understandable by walking you through what
changed, asking for confirmation at critical steps, and verifying the update with CI.

## Prerequisites

- Git working tree must be clean: `git status` should show "nothing to commit"
- Current branch should be main/master (not a feature branch)
- You should have pulled latest changes from origin

## Steps

1. **Verify prerequisites**
   ```bash
   git status                              # must be clean
   git branch --show-current               # should be main or master
   ```
   If the tree is dirty, commit or stash changes. If on a feature branch, switch to main first.

2. **Check if .copier-answers.yml exists**
   ```bash
   test -f .copier-answers.yml && echo "Found" || echo "Not found"
   ```
   If not found, this project wasn't generated via Copier. Update workflow won't work.

3. **Check for available updates**
   ```bash
   copier check-update --quiet
   ```
   Report result: "No updates available" OR "Update available from vX.Y.Z → vA.B.C"

4. **If no update available, stop.** Report: "Project is already on the latest template version."

5. **If update available, show what changed**

   Get the current template version from `.copier-answers.yml`:
   ```bash
   CURRENT_VERSION=$(grep "_version" .copier-answers.yml | sed 's/.*: "\([^"]*\)".*/\1/')
   ```

   Then run:
   ```bash
   copier check-update --quiet --output-format json | jq '.available_version'
   ```

   Show the user: "Ready to update from vX.Y.Z → vA.B.C"

6. **Preview the changes** (show summary)

   Run:
   ```bash
   copier update --dry-run --no-input --conflict inline 2>&1 | head -20
   ```

   Show the user what files will change (e.g., "Will update: pyproject.toml, CLAUDE.md, .github/workflows/lint.yml")

7. **Ask user for confirmation**
   ```
   Ready to update? This will:
   - Update template files (pyproject.toml, justfile, .github/, etc.)
   - Keep your custom changes (README.md, your code, etc.)
   - May create .rej files if conflicts exist

   Continue? (yes/no)
   ```

   If user says "no", stop here.

8. **Run the update**
   ```bash
   copier update --trust --conflict inline
   ```

9. **Check for conflicts**
   ```bash
   find . -name "*.rej" | wc -l
   ```

   If `.rej` files exist:
   - List them: `find . -name "*.rej"`
   - Show user: "Conflicts found. Review these files and manually apply the changes."
   - Exit here — user must resolve conflicts before running CI.

   If merge markers exist in any file:
   - Scan for `<<<<<<` and `>>>>>>`
   - Report which files have conflicts
   - User must resolve before continuing.

10. **If no conflicts, run CI to verify the update**
    ```bash
    just ci
    ```

    If CI passes:
    - ✓ Update successful and verified
    - Commit the changes: `git add . && git commit -m "chore: update from template vX.Y.Z → vA.B.C"`
    - Report success and next steps

    If CI fails:
    - ✗ Update caused test/lint failures
    - Show the failure details
    - User must fix issues (likely: new ruff rules apply, new test requirements, etc.)
    - Re-run `just ci` after fixes

## Output Format

### Success (no conflicts, CI passes)

```
## Template Update — My Library

✓ Update available: vX.Y.Z → vA.B.C

Changes:
- Updated: pyproject.toml, justfile, CLAUDE.md, .github/workflows/
- Kept: README.md, your source code, docs/

✓ Update applied successfully
✓ No conflicts
✓ CI passed (all tests, lint, types, docs)

✓ Changes committed: git log --oneline -1

Next steps:
- Review the changes: git show HEAD
- Push to origin: git push origin main
- Create PR for review if desired

Your project is now synced with the latest template!
```

### Conflicts Detected

```
## Template Update — My Library

✓ Update available: vX.Y.Z → vA.B.C
✓ Update applied

✗ Conflicts found in 2 files:
  - src/my_library/core.py.rej
  - pyproject.toml.rej

Action required:
1. Review the .rej files to see what couldn't be auto-merged
2. Manually apply the changes to the corresponding source files
3. Delete the .rej files
4. Run: git add . && git commit -m "chore: resolve template update conflicts"
5. Run: just ci to verify
```

### CI Failures After Update

```
## Template Update — My Library

✓ Update applied
✓ No conflicts
✗ CI failed at: ruff lint

Error:
  src/my_library/core.py:42: D100 Missing docstring in public module

This is likely due to new standards from the updated template (e.g., new ruff D rules).

Action required:
1. Fix the failures: just review
2. Commit changes: git add . && git commit -m "chore: resolve template update failures"
3. Re-run: just ci to verify
```

## Tips

- Always run this on main/master, not a feature branch
- If conflicts occur, they're usually in `.github/`, not your code
- New ruff rules from template updates are common — just run `/docs-check` or `just review` to fix
- If you customize files like `pyproject.toml`, mark them `_skip_if_exists` in `.copier-answers.yml` before the next update to preserve your changes
- Keep a recent commit before running update, so you can `git revert HEAD` if needed

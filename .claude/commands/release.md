Orchestrate a new release: verify CI, bump version, tag, and push.

This command automates the release workflow for this Copier template repository.

## Prerequisites

- All changes must be committed (no dirty working tree)
- You must have push access to the origin remote
- The main/master branch must be up to date with origin

## Steps

1. **Verify the working tree is clean**
   ```bash
   git status
   ```
   If there are uncommitted changes, commit or stash them before proceeding.

2. **Run the full CI pipeline to ensure everything passes**
   ```bash
   just ci
   ```
   If any step fails (lint, type, test, pre-commit), fix the issue and re-run.
   Do not proceed until `just ci` passes completely.

3. **Determine the version bump**
   Ask the user: "What type of bump? (patch/minor/major) or specify explicit version (X.Y.Z)?"
   - `patch` — bug fixes, no new features (0.0.2 → 0.0.3)
   - `minor` — new features, backwards compatible (0.0.2 → 0.1.0)
   - `major` — breaking changes (0.0.2 → 1.0.0)
   - Explicit version — e.g., "0.1.0-rc1" for pre-releases (use with caution)

4. **Bump the version** using the version bump script
   ```bash
   NEW_VERSION=$(python scripts/bump_version.py --bump patch)
   # OR
   NEW_VERSION=$(python scripts/bump_version.py --new-version X.Y.Z)
   ```
   Output the new version to the user.

5. **Verify the version was bumped correctly**
   ```bash
   grep version pyproject.toml | head -1
   ```
   Confirm the version line matches the new version.

6. **Create a git tag** with the new version
   ```bash
   git tag v${NEW_VERSION}
   ```

7. **Push the tag** to origin (this triggers release.yml)
   ```bash
   git push origin v${NEW_VERSION}
   ```

8. **Monitor the release workflow**
   - The tag push triggers `.github/workflows/release.yml`
   - Wait for the workflow to complete (check GitHub Actions)
   - Confirm that a GitHub Release was created with release notes

## Output

Report to the user:
```
✓ Release v<VERSION> created successfully

Next steps:
- GitHub Release: https://github.com/[org]/python_project_template/releases/tag/v<VERSION>
- Monitor workflow: https://github.com/[org]/python_project_template/actions

To update existing generated projects to this new template version:
  copier update --trust  # in an existing generated-project directory
```

## Rollback (if something goes wrong)

If you need to undo a release before the workflow completes:
```bash
git tag -d v<VERSION>              # delete local tag
git push origin :v<VERSION>        # delete remote tag
# Fix the issue, then run release again
```

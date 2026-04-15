---
description: Orchestrate a new release — verify CI, bump version, tag, and push to origin. Use when the user asks to "release", "cut a release", "ship a version", or "tag and publish".
argument-hint: [patch|minor|major|X.Y.Z]
allowed-tools: Read Bash(git *) Bash(just ci:*) Bash(uv run python scripts/bump_version.py *) Bash(grep *)
disable-model-invocation: true
---

Orchestrate a new release: verify CI, bump version, tag, and push.

## Prerequisites

- All changes must be committed (no dirty working tree)
- You must have push access to origin
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
   This runs: fix → fmt → lint → type → docs-check → test → pre-commit.
   If any step fails, fix the issue and re-run. Do not proceed until all steps pass.

3. **Determine the version bump**
   Ask the user: "What type of bump? (patch/minor/major) or specify explicit version (X.Y.Z)?"
   - `patch` — bug fixes, no new features (0.1.0 → 0.1.1)
   - `minor` — new features, backwards compatible (0.1.0 → 0.2.0)
   - `major` — breaking changes (0.1.0 → 1.0.0)

4. **Bump the version** in `pyproject.toml` using the release script
   ```bash
   # Bump by type (patch / minor / major):
   NEW_VERSION="$(uv run python scripts/bump_version.py --bump patch)"

   # Or set an explicit version:
   NEW_VERSION="$(uv run python scripts/bump_version.py --new-version 1.2.3)"

   echo "New version: ${NEW_VERSION}"
   ```
   The script rewrites `pyproject.toml` in place and prints the new version on stdout.

5. **Verify the version was bumped correctly**
   ```bash
   grep "^version" pyproject.toml
   ```
   Confirm the version matches your intended bump.

6. **Create a commit** for the version bump
   ```bash
   git add pyproject.toml
   git commit -m "chore(release): bump version to X.Y.Z"
   ```

7. **Create a git tag** with the new version
   ```bash
   git tag vX.Y.Z
   ```
   Tags should follow PEP 440 with a `v` prefix (e.g., `v0.2.0`, `v1.0.0-rc1`).

8. **Push the commit and tag** to origin
   ```bash
   git push origin main  # or master, depending on your default branch
   git push origin vX.Y.Z
   ```

9. **Create a GitHub Release** (if not automated)
   - Go to: https://github.com/yourusername/my-library/releases
   - Click "Draft a new release"
   - Select the tag you just pushed
   - Add release notes (summary of changes, new features, breaking changes, etc.)
   - Publish the release

## Output

Report to the user:
```
✓ Release vX.Y.Z created successfully

Release page: https://github.com/yourusername/my-library/releases/tag/vX.Y.Z

Next steps:
- Check that the tag pushed successfully
- Consider updating your CHANGELOG.md if not auto-generated
- Notify users of the new release
```

## Rollback (if something goes wrong)

If you need to undo a release before publishing:
```bash
git reset --soft HEAD~1        # undo the version commit, keep changes staged
git tag -d vX.Y.Z             # delete local tag
# Fix the issue, then run release again
```

If already pushed to origin:
```bash
git tag -d vX.Y.Z             # delete local tag
git push origin :vX.Y.Z       # delete remote tag (colon syntax or git push --delete)
git push origin +<previous-commit>:main  # force-push main back (use with caution!)
```

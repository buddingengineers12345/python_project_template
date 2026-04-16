# pre-commit

pre-commit is a framework for managing Git hooks. It runs configured tools automatically
before each commit, blocking the commit if any check fails.

---

## What it does

- Installs hooks into `.git/hooks/` on `pre-commit install`
- On `git commit`, runs each hook against staged files only (fast)
- In CI, run against all files with `pre-commit run --all-files`

---

## Installation

```bash
pip install pre-commit     # or: uv add --dev pre-commit
pre-commit install         # installs the git hook — run once per clone
```

Verify the hook was installed:
```bash
cat .git/hooks/pre-commit   # should reference pre-commit
```

---

## Complete .pre-commit-config.yaml

This is the canonical config for all tools in this project. See
`references/complete-configs.md` for a copy you can paste directly.

```yaml
# Minimum pre-commit version required.
minimum_pre_commit_version: "3.0.0"

# Default Python version used when a hook doesn't specify one.
default_language_version:
  python: python3.11

repos:
  # ── Ruff: lint + format ──────────────────────────────────────────────────
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.0                  # pin to a specific tag
    hooks:
      - id: ruff
        args: ["--fix"]          # auto-fix safe issues on commit
      - id: ruff-format          # auto-format on commit

  # ── Bandit: security lint ─────────────────────────────────────────────────
  - repo: https://github.com/PyCQA/bandit
    rev: 1.8.3
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
        # Scope to src/ only — test code legitimately uses assert, subprocess, etc.
        files: ^src/

  # ── Semgrep: pattern-based security scan ─────────────────────────────────
  - repo: https://github.com/semgrep/semgrep
    rev: v1.60.0                 # pin to a specific release
    hooks:
      - id: semgrep
        args: ["--config", ".semgrep.yml", "--error"]
        files: ^src/
        # pass_filenames: true is correct for per-file analysis.
        # Cross-file taint rules require running semgrep outside pre-commit (in CI).

  # ── basedpyright: type checking ──────────────────────────────────────────
  # Runs as a `local` hook so it uses the project's installed venv.
  # Requires basedpyright to be installed: pip install basedpyright
  - repo: local
    hooks:
      - id: basedpyright
        name: basedpyright
        entry: basedpyright
        language: system         # uses whatever basedpyright is on PATH
        types: [python]
        pass_filenames: false    # basedpyright analyses the whole project graph

  # ── General hygiene ──────────────────────────────────────────────────────
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-merge-conflict
      - id: debug-statements      # catches leftover breakpoint() / pdb.set_trace()
```

### Hook ordering rationale

Hooks run in the order listed. Fast, auto-fixing hooks go first so the developer sees
clean output; slow analysis hooks (basedpyright) go last.

```
ruff (fix + format)  →  bandit  →  semgrep  →  basedpyright  →  hygiene
```

---

## Running pre-commit

```bash
# Run all hooks against all files (use after install or config changes):
pre-commit run --all-files

# Run a specific hook only:
pre-commit run ruff --all-files
pre-commit run bandit --all-files
pre-commit run semgrep --all-files
pre-commit run basedpyright --all-files

# Run against staged files only (mirrors what git commit does):
pre-commit run

# Run against a specific file:
pre-commit run --files src/mymodule.py
```

---

## Skipping hooks

**Skip all hooks for one commit** (use very rarely — e.g. emergency hotfix):
```bash
git commit --no-verify -m "emergency: revert broken deploy"
```

**Skip a specific hook for one commit:**
```bash
SKIP=basedpyright git commit -m "wip: partially typed module"
SKIP=semgrep,bandit git commit -m "temp: adding fixture with insecure pattern"
```

**Exclude files permanently** in the hook config:
```yaml
- id: ruff
  exclude: "^tests/fixtures/"   # regex matched against the file path
```

---

## Updating hook versions

Always pin `rev:` to a tagged release. Update intentionally:

```bash
# Update all hooks to latest tagged release:
pre-commit autoupdate

# Update a single repo:
pre-commit autoupdate --repo https://github.com/astral-sh/ruff-pre-commit
```

After updating, run `pre-commit run --all-files` to confirm nothing broke.

---

## CI integration (GitHub Actions)

Use the dedicated action — it caches hook environments automatically:

```yaml
- name: Run pre-commit
  uses: pre-commit/action@v3.0.1
```

This caches `~/.cache/pre-commit` keyed on the hash of `.pre-commit-config.yaml`.

**Important for `language: system` hooks** (basedpyright): the hook runs whatever is on
`PATH`, so project dependencies must be installed *before* pre-commit runs:

```yaml
- name: Install Python dependencies
  run: pip install -r requirements.txt   # or: uv sync — must include basedpyright

- name: Run pre-commit
  uses: pre-commit/action@v3.0.1
```

If you run individual tool steps (ruff, basedpyright, etc.) as separate CI jobs, the
pre-commit job is optional but still useful as a final gate — it catches hooks that
aren't individually tested.

---

## Adding a new hook

1. Find the hook repo at [pre-commit.com/hooks](https://pre-commit.com/hooks.html) or
   the tool's own docs.
2. Add a `- repo:` block to `.pre-commit-config.yaml` in the appropriate position
   (fast/auto-fixing hooks first, slow analysis hooks last).
3. Pin `rev:` to a tagged release — never `HEAD` or a branch name.
4. Run `pre-commit run --all-files` to validate.
5. Add the tool to the table in `SKILL.md` and create `references/<toolname>.md`.
6. Copy the updated full config to `references/complete-configs.md`.

---

## Gotchas

- **Staged-only mode can hide issues.** On commit, pre-commit checks staged files only.
  Unstaged changes interacting with staged ones can produce a passing local commit that
  fails CI (which runs `--all-files`). Always run `pre-commit run --all-files` before
  pushing to a shared branch.
- **`language: system` hooks depend on PATH.** The basedpyright hook uses whatever
  `basedpyright` is on `PATH`. If your venv isn't activated, it either uses a wrong
  version or fails entirely. In CI, install dependencies before running pre-commit.
- **Cache in `~/.cache/pre-commit`.** If a hook behaves strangely after a version bump,
  clear it: `pre-commit clean`. Then re-run `pre-commit install`.
- **`pass_filenames: false` is required for whole-project tools.** basedpyright resolves
  the full import graph; passing individual filenames breaks cross-module type inference.
  Semgrep's per-file mode (`pass_filenames: true`) is fine for single-file rules but
  won't catch cross-file taint flows — run those in CI without pre-commit.
- **`rev` must be a tag.** pre-commit warns if you use a branch; tags guarantee
  reproducibility across machines and CI runs.

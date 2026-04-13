# Copier Template Conventions

# applies-to: copier.yml, template/**

These rules apply to `copier.yml` and all files under `template/`. They are
specific to the template meta-repo and are **not** propagated to generated projects.

## copier.yml structure

Organise `copier.yml` into clearly labelled sections with separator comments:

```yaml
# --- Template metadata ---
_min_copier_version: "9.11.2"
_subdirectory: template

# --- Jinja extensions ---
_jinja_extensions:
  - jinja2_time.TimeExtension

# --- Questions / Prompts ---
project_name:
  type: str
  help: Human-readable project name

# --- Computed values ---
current_year:
  type: str
  when: false
  default: "{% now 'utc', '%Y' %}"

# --- Post-generation tasks ---
_tasks:
  - command: uv lock
```

## Questions (prompts)

- Every question must have a `help:` string that clearly explains what the value is used for.
- Every question must have a sensible `default:` so users can accept defaults with `--defaults`.
- Use `choices:` for questions with a fixed set of valid answers (license, Python version).
- Use `validator:` with a Jinja expression for format validation (e.g. package name must be
  a valid Python identifier).
- Use `when: "{{ some_bool }}"` to conditionally show questions that are only relevant
  when a related option is enabled.

## Computed variables

Computed variables (not prompted) must use `when: false`:

```yaml
current_year:
  type: str
  when: false
  default: "{% now 'utc', '%Y' %}"
```

They are not stored in `.copier-answers.yml` and not shown to users. Use them for
derived values (year, Python version matrix) to keep templates DRY.

## Secrets and third-party tokens

Do **not** add Copier prompts for API tokens or upload keys (Codecov, PyPI, npm,
and so on). Those belong in the CI provider’s **encrypted secrets** (for example
GitHub Actions **Settings → Secrets**) and in maintainer documentation
(`README.md`, `docs/ci.md`), not in `.copier-answers.yml`.

If you must accept a rare secret interactively, use `secret: true` with a safe
`default` so it is **not** written to the answers file — and still prefer
documenting the secret-in-CI workflow instead of prompting.

## _skip_if_exists

Files in `_skip_if_exists` are preserved on `copier update` — user edits are not
overwritten. Add a file here when:
- The user is expected to customise it significantly (`pyproject.toml`, `README.md`).
- Overwriting it on update would destroy user work.

Do **not** add files here unless there is a clear reason. Too many skipped files
make updates less useful.

## _tasks

Post-generation tasks run after both `copier copy` and `copier update`. Design them
to be **idempotent** (safe to run multiple times) and **fast** (do not download
large artefacts unconditionally).

Use `copier update --skip-tasks` to bypass tasks when only the template content needs
to be refreshed.

Tasks use `/bin/sh` (POSIX shell), not bash. Use POSIX-compatible syntax.

## Template file conventions

- Add `.jinja` suffix to every file that contains Jinja2 expressions.
- Files without `.jinja` are copied verbatim (no Jinja processing).
- Template file names may themselves contain Jinja expressions:
  `src/{{ package_name }}/__init__.py.jinja` → `src/mylib/__init__.py`.
- Keep Jinja expressions in file names simple (variable substitution only).

## .copier-answers.yml

- Never edit `.copier-answers.yml` by hand in generated projects.
- The answers file is managed by Copier's update algorithm. Manual edits cause
  unpredictable diffs on the next `copier update`.
- The template file `{{_copier_conf.answers_file}}.jinja` generates the answers file.
  Changes to its structure require careful migration testing.

## Versioning and releases

- Tag releases with **PEP 440** versions: `1.0.0`, `1.2.3`, `2.0.0a1`.
- `copier update` uses these tags to select the appropriate template version.
- Introduce `_migrations` in `copier.yml` when a new version renames or removes template
  files, to guide users through the update.
- See `src/{{ package_name }}/common/bump_version.py` and `.github/workflows/release.yml` for the release
  automation workflow.

## Skill descriptions (if adding skills to template)

Every skill SKILL.md frontmatter must include a `description:` field with these constraints:

- **Max 1024 characters** (hard limit) — skill descriptions are used in Claude's command
  suggestions and UI; longer descriptions are truncated and unusable.
- Use `>-` for multi-line descriptions (block scalar without trailing newline).
- Lead with the skill's **primary purpose** (what it does).
- Include **trigger keywords** if applicable (e.g., "use this when the user says...").
- Mention **what the skill outputs** (e.g., "produces test skeletons with AAA structure").

**Template:**

```yaml
---
name: skill-name
description: >-
  <Primary purpose in one sentence.>

  <When to use it / trigger keywords.>

  <What it produces or outputs.>
---
```

**Example (tdd-test-planner):**

```yaml
description: >-
  Convert a requirement into a structured pytest test plan.
  Use when the user says: "plan my tests", "write tests first", "TDD approach".
  Produces categorised test cases (happy path, errors, boundaries, edges, integration)
  plus pytest skeletons with AAA structure and fixture guidance.
```

**Measurement:** Count characters in the `description:` value (not including frontmatter).

---

## Dual-hierarchy maintenance

This repo has two parallel `.claude/` trees:

```
.claude/                  ← used while developing the template
template/.claude/         ← rendered into generated projects
```

When adding or modifying hooks, commands, or rules:
- Decide whether the change applies to the template maintainer only, generated projects
  only, or both.
- If both: add to both trees. The `post-edit-template-mirror.sh` hook will remind you.
- Rules specific to Copier/Jinja/YAML belong only in the root tree.
- Rules for Python/Bash/Markdown typically belong in both trees.

## Testing template changes

Every change to `copier.yml` or a template file requires a test update in
`tests/test_template.py`. Run:

```bash
just test    # run all template tests
copier copy . /tmp/test-output --trust --defaults --vcs-ref HEAD
```

Clean up: `rm -rf /tmp/test-output`

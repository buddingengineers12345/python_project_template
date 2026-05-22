# Generating and Updating Projects from the Template

## Generating a test project from the template

To manually generate a project and inspect the output:

```bash
copier copy . /tmp/test-output --trust --defaults
```

To pass specific answers non-interactively:

```bash
copier copy . /tmp/test-output --trust \
  --data project_name="My Library" \
  --data include_docs=false \
  --data include_pandas_support=false
```

Clean up afterward: `rm -rf /tmp/test-output`

When iterating on an **uncommitted** local template, use **`copier copy --vcs-ref HEAD . DESTINATION`**
so Copier uses the current tree (otherwise it may select the latest PEP 440 tag and skip dirty files).

## Copy vs update (important)

- **Generate** a new project: `copier copy TEMPLATE DESTINATION`.
- **Update** an existing generated project to the latest template version: `copier update`.
- **`copier recopy`**: reapplies the template and keeps answers; does **not** use the smart merge
  algorithm. Prefer `copier update` for normal sync.

For updates, Copier works best when:

1. The template includes a valid `.copier-answers.yml`.
2. The template is versioned with git tags (PEP 440 versions).
3. The destination folder is versioned with git.

Useful flags: **`copier update --defaults`**, **`--data` / `--data-file`** for selective answer changes,
**`--vcs-ref=:current:`** to re-record answers without changing template version, **`copier check-update`**
(JSON via **`--output-format json`**, **`--quiet`** exit code `2` when an update exists).

### Never edit `.copier-answers.yml` by hand

Do not manually change the answers file (`.copier-answers.yml`, controlled by `_answers_file` in
`copier.yml`). The update algorithm relies on it and manual edits can lead to unpredictable diffs.

### Handle update conflicts

Default **`--conflict inline`** produces merge-style markers in files; **`--conflict rej`** writes
`*.rej` sidecars. Generated projects ship pre-commit hooks for both patterns (`check-merge-conflict`
and a fail-on-`*.rej` hook). Review conflicts before committing.

### Template `_tasks` on copy vs update

Post-generation **`_tasks`** in `copier.yml` run after both **`copier copy`** and **`copier update`**
(intentionally, so `uv.lock` and the dev environment stay aligned). Use **`copier update --skip-tasks`**
when you need to skip them.

### Maintainer: releases and `_migrations`

Tag releases with **PEP 440**-compatible versions so consumers' `copier update` picks the right template
revision. Introduce **`_migrations`** in `copier.yml` when you need scripted steps across template
versions (e.g. renaming generated paths). Prefer SSH or credential-free Git URLs so `_src_path` in
answers files stays clean. Shallow template clones in CI can increase Git work for Copier; use full
clones if you hit resource issues.

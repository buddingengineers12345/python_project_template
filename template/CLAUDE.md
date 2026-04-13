# template/ — Jinja2 Template Source

This directory is the **Copier template subdirectory** (`_subdirectory: template` in `copier.yml`).
Everything here is rendered by Copier into the destination project. Files with a `.jinja` suffix are
processed as Jinja2; files without it are copied verbatim.

> [!IMPORTANT]
> Do **not** run Python or shell tools directly inside this directory — it is source material,
> not executable code. To test rendering, use `copier copy . /tmp/test-output --trust --defaults --vcs-ref HEAD`.

## Directory layout

```
template/
├── src/{{ package_name }}/          # Generated Python package
│   ├── __init__.py.jinja
│   ├── core.py.jinja                # Core module skeleton
│   ├── {% if include_cli %}cli.py{% endif %}.jinja   # Typer CLI (optional)
│   └── common/                      # Shared utilities (always included)
│       ├── __init__.py.jinja
│       ├── bump_version.py.jinja    # PEP 440 version bumper (_skip_if_exists); ruff ignores D+T20 in pyproject
│       ├── decorators.py.jinja      # Retry, timing, and other decorators
│       ├── file_manager.py.jinja    # File I/O helpers
│       ├── logging_manager.py.jinja # structlog setup (HUMAN / LLM modes)
│       └── utils.py.jinja           # Miscellaneous utilities
│
├── tests/                           # Generated test suite
│   ├── conftest.py.jinja
│   ├── test_imports.py.jinja        # Smoke test: package is importable
│   └── {{ package_name }}/
│       ├── test_core.py.jinja
│       └── test_support.py.jinja    # Tests for common/* utilities
│
├── docs/                            # MkDocs source (conditional on include_docs)
│   ├── {% if include_docs %}index.md{% endif %}.jinja
│   └── {% if include_docs %}ci.md{% endif %}.jinja
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml.jinja             # Main test matrix (Python 3.11–3.13)
│   │   ├── lint.yml.jinja           # Ruff + basedpyright on PRs
│   │   ├── dependency-review.yml.jinja  # Dependency diff review on PRs (optional)
│   │   ├── docs.yml.jinja           # MkDocs deploy to gh-pages (conditional)
│   │   ├── pre-commit-update.yml.jinja  # Weekly pre-commit autoupdate
│   │   ├── release.yml.jinja        # Version bump + GitHub Release (conditional)
│   │   └── security.yml.jinja       # CodeQL + pip-audit (conditional)
│   ├── ISSUE_TEMPLATE/              # Bug report + feature request templates
│   ├── CODE_OF_CONDUCT.md.jinja
│   ├── CODEOWNERS.jinja
│   ├── github-branch-protection.md.jinja  # Maintainer checklist: PR-only main, squash merges
│   ├── PULL_REQUEST_TEMPLATE.md.jinja
│   └── renovate.json.jinja
│
├── .claude/                         # Claude Code config for generated projects
│   ├── settings.json                # Hooks + permissions (static — not .jinja)
│   ├── hooks/                       # Shell hooks for generated project dev
│   ├── commands/                    # Slash commands (.md and .md.jinja)
│   ├── rules/                       # AI rules (common, python, bash, markdown)
│   └── skills/                      # Agent skills (pytest, docstrings, etc.)
│
├── .vscode/                         # VS Code settings + launch configs
├── pyproject.toml.jinja             # Package metadata, deps, ruff, basedpyright config
├── justfile.jinja                   # Task runner for generated projects
├── CLAUDE.md.jinja                  # Project-specific CLAUDE.md (rendered on copy)
├── README.md.jinja
├── CONTRIBUTING.md.jinja
├── SECURITY.md.jinja
├── LICENSE.jinja
├── env.example.jinja
├── .gitignore.jinja
├── .pre-commit-config.yaml.jinja
├── .secrets.baseline                # detect-secrets baseline (verbatim)
├── {{_copier_conf.answers_file}}.jinja  # Copier answers file template
└── {% if include_git_cliff %}cliff.toml{% endif %}.jinja
```

## Key Copier variables used in templates

| Variable | Type | Purpose |
|---|---|---|
| `project_name` | str | Human-readable name (e.g. "My Library") |
| `project_slug` | str | URL/dist slug (lowercase, hyphens) |
| `package_name` | str | Python identifier (underscores) |
| `project_description` | str | One-line description |
| `author_name` / `author_email` | str | Package metadata |
| `github_username` | str | GitHub org/user for workflow URLs |
| `python_min_version` | str | `"3.11"`, `"3.12"`, or `"3.13"` |
| `license` | str | MIT, Apache-2.0, BSD-3-Clause, GPL-3.0, Proprietary |
| `include_docs` | bool | Add MkDocs + docs workflows |
| `include_pandas_support` | bool | Add pandas to dependencies |
| `include_numpy` | bool | Add NumPy to dependencies |
| `include_release_workflow` | bool | Add release.yml workflow |
| `include_pypi_publish` | bool | PyPI OIDC publishing in release (needs `include_release_workflow`) |
| `include_security_scanning` | bool | Add CodeQL + pip-audit workflow |
| `include_cli` | bool | Add Typer CLI entry point |
| `include_git_cliff` | bool | Add git-cliff + cliff.toml + `just changelog` |
| `current_year` | str | Computed: `{% now 'utc', '%Y' %}` |
| `github_actions_python_versions` | str | Computed: JSON array from `python_min_version` |

## Jinja2 conventions in this directory

- Use `{{ variable_name }}` for substitution.
- Use `{% if condition %}…{% endif %}` for conditional blocks.
- File names may themselves be Jinja expressions: `src/{{ package_name }}/__init__.py.jinja`.
- The `jinja2_time.TimeExtension` (`{% now %}`), `jinja2.ext.do`, and `jinja2.ext.loopcontrols`
  extensions are enabled.
- The `pre-write-jinja-syntax.sh` hook validates Jinja2 syntax before writing `.jinja` files.
- The `post-edit-jinja.sh` hook re-validates after every edit.

## Dual `.claude/` hierarchy

This directory has its own `.claude/` tree that is rendered into generated projects:

```
template/.claude/   ← rendered into GENERATED projects
.claude/            ← used while DEVELOPING this template repo (root)
```

The generated-project `.claude/` has fewer hooks (no SessionStart, no Jinja/Copier-specific
hooks, no Stop hooks). It does have: Python post-edit hook, markdown guard, no-verify blocker,
push reminder, commit quality scan, config/lock protection, strict TDD enforcement
(`pre-write-src-require-test.sh`), a commit-time coverage gate warning
(`pre-bash-coverage-gate.sh`), and a refactor test reminder (`post-edit-refactor-test-guard.sh`).

## Testing template changes

After any change to a `.jinja` file or `copier.yml`:

1. Run the test suite: `just test`
2. Manually inspect output: `copier copy . /tmp/test-output --trust --defaults --vcs-ref HEAD`
3. Clean up: `rm -rf /tmp/test-output`

Every new Copier variable or template file must have a corresponding test in
`tests/test_template.py`.

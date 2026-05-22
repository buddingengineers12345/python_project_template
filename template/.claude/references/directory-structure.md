# Directory Structure

```
.
├── template/                 # Jinja2 source files that Copier renders
│   ├── src/{{ package_name }}/   # Generated package source (common/, core.py, cli.py…)
│   ├── tests/                # Generated project test suite
│   ├── .claude/              # Claude hooks/commands/rules/skills for generated projects
│   ├── .github/workflows/    # Generated CI/CD workflows
│   └── …                    # pyproject.toml.jinja, justfile.jinja, CLAUDE.md.jinja, …
├── tests/                    # pytest suite for this meta-repo (see tests/CLAUDE.md)
│   ├── script_imports.py     # REPO_ROOT + load_script_module() for unit tests importing scripts/
│   ├── conftest.py           # top-level shared fixtures
│   ├── unit/                 # fast isolated script tests
│   ├── integration/          # Copier copy/update integration suite
│   └── e2e/                  # end-to-end tests (placeholder)
├── scripts/                  # Automation scripts for CI or local tasks (see scripts/CLAUDE.md)
│   ├── repo_file_freshness.py    # Git-based freshness dashboard (→ docs/ + assets/)
│   ├── bump_version.py           # PEP 440 version bumper (patch/minor/major)
│   ├── check_root_template_sync.py  # Root ↔ template parity (workflows, settings, recipes)
│   ├── pr_commit_policy.py       # PR title/body + commit message policy (CI)
│   └── sync_skip_if_exists.py    # Sync copier.yml _skip_if_exists with template paths
├── .claude/                  # Claude Code hooks, commands, and rules for THIS meta-repo
│   ├── settings.json         # Hook registrations and permission allow/deny lists
│   ├── hooks/                # Shell hook scripts (see hooks/README.md)
│   ├── commands/             # Slash command prompts (/review, /generate, /release, …)
│   └── rules/                # AI rules (common/, python/, jinja/, bash/, yaml/, copier/)
├── docs/                     # Markdown output folder (repo_file_status_report.md, etc.)
├── assets/                   # Freshness JSON artifacts (file_freshness.json, etc.)
├── .github/                  # Meta-repo GitHub Actions workflows
├── copier.yml                # Template prompts, computed vars, and post-gen tasks
├── justfile                  # Task runner (use `just` not raw commands)
├── pyproject.toml            # Dev deps for THIS repo (not for generated projects)
├── .pre-commit-config.yaml   # Pre-commit hooks for meta-repo
└── uv.lock                   # Committed lockfile — never delete
```

# Recent Improvements (April 2026)

## Standards enforcement (this PR)
- Added `D` (pydocstyle, Google convention), `C90` (McCabe complexity), `PERF` (perflint) to ruff rules
- Added `per-file-ignores` so `tests/**` and `scripts/**` ignore `T20` only (`print`); docstrings (`D`) apply;
  generated projects enforce Google docstrings on `src/**/common/bump_version.py` like the rest of `src/`
- Added `[tool.ruff.lint.mccabe]` max-complexity = 10
- Enhanced basedpyright config: `standard` mode, lenient with external stubs
- Added `pytest-cov` + `coverage[toml]` to dev dependencies
- Added `just docs-check` and `just review` recipes; `just ci` now includes docs-check
- Added `.claude/hooks/post-edit-python.sh` and `post-edit-jinja.sh` (PostToolUse hooks)
- Added five new Claude commands: `/review`, `/coverage`, `/docs-check`, `/standards`, `/update-claude-md`
- Added Standards Enforcement section to CLAUDE.md (definition of done, tooling table, command table)
- Propagated all of the above into `template/` so generated projects inherit the same enforcement

## Package structure
- Renamed `_support` package to `common` for clearer semantics
- Refactored support utilities into dedicated modules: `file_manager`, `logging_manager`, `decorators`, `utils`
- Enhanced logging manager with level-aware log functions for all severity levels

## Testing enhancements
- Added comprehensive test coverage for `common` utilities (`test_support.py`)
- Improved test organization with new `tests/` directory structure in generated projects
- Added parametrized tests for license rendering and feature combinations

## CI/CD improvements
- Updated GitHub Actions workflow versions for better compatibility
- Added `--frozen` flag to `uv sync/update` recipes for reproducible builds
- Added pre-commit hook to reject Copier rejection files (`*.rej`)
- Enhanced test matrix to include Python 3.13 testing

## Documentation scaffolding
- Added `docs/` directory template with MkDocs structure
- Added `index.md.jinja` documentation template
- Added `.claude/` commands for template-specific automation

## Release automation
- Added `release.yml` GitHub Actions workflow for automated version bumping and releases
- Integrated `scripts/bump_version.py` for PEP 440 version management
- Template now supports manual release triggering with configurable bump strategy

## Claude documentation update (April 2026)
- Updated root `CLAUDE.md`: accurate `just ci` pipeline description, complete justfile recipe table,
  added `T20` ruff rule, full hooks table, full slash-commands table, expanded directory structure
- Fixed `template/CLAUDE.md.jinja`: corrected basedpyright mode from "strict" to "standard",
  added `/release` slash command entry
- Added `CLAUDE.md` in `template/` — explains Jinja2 source layout, Copier variables, dual `.claude/` hierarchy
- Added `CLAUDE.md` in `tests/` — explains test patterns, helpers, categories, and how to add new tests
- Added `CLAUDE.md` in `scripts/` — documents each script, CLI flags, outputs, and CI integration
- Documented hooks and rules in `.claude/hooks/README.md` and `.claude/rules/README.md` (dual hierarchy with `template/.claude/`)
- Added `CLAUDE.md` in `.github/` — documents all meta-repo workflows and design principles

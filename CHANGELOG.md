# Changelog

All notable changes to this project will be documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-04

### Added

- **Generated projects:** `structlog`-based logging with human-readable and LLM-oriented output modes (replacing stdlib logging defaults where applicable).
- **Claude automation:** commands for release, dependency, and update workflows alongside existing review and standards tooling.
- **Standards enforcement:** Claude-side guidance and hooks to align generated projects with coding, testing, and documentation expectations.

## [0.0.2] - 2026-04-03

### Fixed

- **Generated projects:** template tests under `test_support` now import the `common` package instead of the removed `_support` module path.

### Changed

- **Documentation:** expanded `README.md` and `CLAUDE.md` with Copier copy/update guidance, maintainer notes (PEP 440 tags, `_migrations`, releases), and a summary of recent template improvements.
- **Lockfile:** refreshed `uv.lock` so `uv sync --frozen` stays aligned with `pyproject.toml`.
- **Changelog:** normalized formatting for pre-commit (`end-of-file-fixer`).

## [0.0.1] - 2026-04-02

### Added

- Initial release of the Copier template repository.
- GitHub Actions workflows for linting, testing, and a manual release workflow.
- Template scaffolding for a modern `uv`-first Python project (optional docs, strict typing, and tests).

[0.1.0]: https://github.com/buddingengineers12345/python_project_template/compare/v0.0.2...v0.1.0
[0.0.2]: https://github.com/buddingengineers12345/python_project_template/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/buddingengineers12345/python_project_template/releases/tag/v0.0.1

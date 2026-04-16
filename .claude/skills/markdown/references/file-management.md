# File management and documentation systems

Covers: file naming conventions, repository folder structure, standard Markdown
files (README, CHANGELOG, CONTRIBUTING, etc.), versioning, commit conventions,
documentation system design, and maintenance.

**Sources:** [Google Markdown Style Guide](https://google.github.io/styleguide/docguide/style.html),
[Folder Structure Conventions](https://github.com/kriasoft/Folder-Structure-Conventions),
[README — Wikipedia](https://en.wikipedia.org/wiki/README),
[Building a Markdown-Based Documentation System](https://medium.com/@rosgluk/building-a-markdown-based-documentation-system-72bef3cb1db3)

---

## File Naming Conventions

### Standard Repository Files (UPPERCASE)

The following well-known files use UPPERCASE names by convention — this ensures
they sort near the top of ASCII-ordered directory listings and are immediately
recognisable:

| File | Purpose |
|---|---|
| `README.md` | Project overview, installation, usage, badges |
| `CHANGELOG.md` | Version history and release notes |
| `CONTRIBUTING.md` | How to contribute to the project |
| `CODE_OF_CONDUCT.md` | Community behaviour standards |
| `SECURITY.md` | Vulnerability reporting policy |
| `LICENSE` | Licence text (plain text, no `.md` extension) |
| `SUMMARY.md` | GitBook / documentation table of contents |
| `SUPPORT.md` | Where to get help |

These files should be placed in the **root directory** of the repository.

### Non-Standard Documentation Files (lowercase-hyphenated)

Any documentation that is not one of the standard files above should use
**lowercase letters with hyphens** as word separators:

```
docs/getting-started.md        ✅
docs/api-reference.md          ✅
docs/configuration-guide.md    ✅
docs/myAdditionalDoc.md        ✅  (camelCase also acceptable for non-standard)

docs/Getting Started.md        ❌  (spaces break URLs)
docs/API_Reference.md          ❌  (underscores less URL-friendly)
docs/APIreference.md           ❌  (hard to read)
```

### Naming Rules

- Use only **lowercase letters, digits, and hyphens** in non-standard file names.
- **No spaces** — spaces must be percent-encoded in URLs (`%20`) and break many tools.
- **No special characters**: `! @ # $ % ^ & * ( ) = + [ ] { } | \ ; ' " , < > ?`
- Use **printable ASCII only** — URI paths are case-sensitive; some file systems are not.
- Keep names **short and descriptive**: `getting-started.md` not `a-guide-to-getting-started-with-this-project.md`.
- Prefer **nouns** for reference docs and **verb phrases** for guides:
  `configuration.md`, `deploy-to-production.md`.

---

## Repository Folder Structure

### Minimal Structure (small project)

```
project/
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── docs/
    ├── getting-started.md
    └── api-reference.md
```

### Standard Structure (medium project)

```
project/
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── LICENSE
├── docs/
│   ├── README.md          ← docs index / overview
│   ├── getting-started.md
│   ├── configuration.md
│   ├── api/
│   │   ├── README.md
│   │   └── endpoints.md
│   └── guides/
│       ├── deploy.md
│       └── troubleshooting.md
├── assets/
│   └── images/
└── src/
```

### Documentation-Only Repository or GitBook

```
docs/
├── README.md              ← introduction / overview
├── SUMMARY.md             ← table of contents (GitBook)
├── chapter-1/
│   ├── README.md          ← chapter introduction
│   └── subsection.md
└── chapter-2/
    ├── README.md
    └── subsection.md
```

### Rules

- Store all non-standard docs under a `docs/` folder to avoid cluttering the root namespace.
- Each subdirectory in `docs/` should have its own `README.md` as an index/overview.
- Use short lowercase names for top-level directories except the standard files.
- `assets/` or `static/` for images, diagrams, and other media files.

---

## Standard File Templates

### README.md

A project README should answer four questions a new visitor has:

```markdown
# Project Name

One-sentence description of what this project does and who it is for.

## Features

- Key feature one
- Key feature two
- Key feature three

## Quick Start

\```bash
npm install my-project
my-project --help
\```

## Documentation

- [Getting Started](docs/getting-started.md)
- [API Reference](docs/api-reference.md)
- [Configuration](docs/configuration.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE) © Your Name
```

**README sections to consider (include what is relevant):**

- Project name and tagline
- Badges (build status, coverage, version, licence)
- Description / what it does
- Features list
- Quick start / installation
- Usage examples (with code blocks)
- Documentation index / links
- Configuration reference (brief, or link out)
- Contributing guide link
- Acknowledgements / credits
- Licence

### CHANGELOG.md

Follow [Keep a Changelog](https://keepachangelog.com/) conventions:

```markdown
# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- New feature description

## [2.1.0] — 2024-01-15

### Added
- User group management API
- Batch processing endpoint

### Changed
- Improved authentication flow performance

### Fixed
- Resolved race condition in session handling (#123)

### Deprecated
- `GET /api/v1/users` — use `GET /api/v2/users` instead

### Removed
- Legacy XML response format

### Security
- Updated dependency X to patch CVE-2024-XXXX

## [2.0.0] — 2024-01-01

### Changed
- **Breaking:** Refactored authentication API (see migration guide)

[Unreleased]: https://github.com/org/repo/compare/v2.1.0...HEAD
[2.1.0]: https://github.com/org/repo/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/org/repo/releases/tag/v2.0.0
```

**Change types (use consistently):**
`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`

### CONTRIBUTING.md

```markdown
# Contributing to Project Name

Thank you for considering contributing!

## Ways to Contribute

- Report bugs via [GitHub Issues](https://github.com/org/repo/issues)
- Suggest features or improvements
- Submit pull requests

## Development Setup

\```bash
git clone https://github.com/org/repo.git
cd repo
npm install
npm test
\```

## Pull Request Process

1. Fork the repository and create a feature branch.
2. Write or update tests for your changes.
3. Ensure all tests pass: `npm test`
4. Update `CHANGELOG.md` under `[Unreleased]`.
5. Submit a pull request with a clear description.

## Code of Conduct

This project follows our [Code of Conduct](CODE_OF_CONDUCT.md).
```

---

## Versioning Blocks in Documentation

For API and library documentation, embed version information clearly:

```markdown
---
title: API Authentication Guide
version: 2.1.0
last_updated: 2024-01-15
author: Documentation Team
---

> **Version note:** This document applies to API v2.1.0 and above.
> For older versions, see the [archived documentation](./archive/).
```

---

## Commit Message Conventions for Documentation Changes

```
docs: update API authentication guide

- Add OAuth 2.0 example with PKCE flow
- Fix broken code sample in section 3
- Update related links

Closes #123
```

**Commit type prefixes:**

| Prefix | Use for |
|---|---|
| `docs` | Documentation changes |
| `feat` | Documentation for a new feature |
| `fix` | Fix incorrect or broken documentation |
| `style` | Formatting-only changes (no content change) |
| `refactor` | Restructure documentation without content change |
| `chore` | Tooling, build, or configuration changes |

---

## Documentation Versioning Strategy

### Inline Versioning (small projects)

Mark version applicability inline in the document:

```markdown
> **Available since v1.4.0**

> **Deprecated in v2.0.0** — use `newMethod()` instead.
```

### Changelog-Based (most projects)

Maintain a single `CHANGELOG.md` as described above.

### Versioned Subdirectories (large / enterprise projects)

```
docs/
├── v2/                   ← current version
│   └── api-reference.md
├── v1/                   ← archived version
│   └── api-reference.md
└── README.md             ← links to current version
```

---

## Documentation Maintenance Rules

- **Delete stale content frequently** and in small batches — stale docs are worse than no docs.
- **Audit links periodically** — broken links erode reader trust.
- **Keep docs close to the code** they describe — co-located docs get updated when code changes.
- **Split documents** that exceed ~500 lines into focused sub-documents with an index.
- **Review documentation** as part of every pull request that changes behaviour.
- **Test code examples** in your docs (use CI where possible) — outdated examples mislead users.
- For docs systems: use GitHub Actions or similar CI to build, lint, and check links automatically.

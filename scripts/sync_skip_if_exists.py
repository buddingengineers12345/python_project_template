#!/usr/bin/env python3
"""Keep ``_skip_if_exists`` in ``copier.yml`` aligned with the template and git history.

This script is intended for scheduled automation (see ``.github/workflows/sync-skip-if-exists.yml``).
It merges a curated base list with paths inferred from frequently touched template sources so
user-editable files stay protected on ``copier update``.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Template-relative paths (POSIX) → destination path literals for ``_skip_if_exists`` (after render).
# ``{{ package_name }}`` is preserved for Copier/Jinja output paths.
TEMPLATE_PATH_TO_SKIP_ENTRY: dict[str, str] = {
    "template/env.example.jinja": "env.example",
    "template/README.md.jinja": "README.md",
    "template/CONTRIBUTING.md.jinja": "CONTRIBUTING.md",
    "template/SECURITY.md.jinja": "SECURITY.md",
    "template/CLAUDE.md.jinja": "CLAUDE.md",
    "template/pyproject.toml.jinja": "pyproject.toml",
    "template/mkdocs.yml.jinja": "mkdocs.yml",
    "template/src/{{ package_name }}/__init__.py.jinja": "src/{{ package_name }}/__init__.py",
    "template/.github/PULL_REQUEST_TEMPLATE.md.jinja": ".github/PULL_REQUEST_TEMPLATE.md",
    "template/.github/CODE_OF_CONDUCT.md.jinja": ".github/CODE_OF_CONDUCT.md",
    "template/.github/ISSUE_TEMPLATE/bug_report.md.jinja": ".github/ISSUE_TEMPLATE/bug_report.md",
    "template/.github/ISSUE_TEMPLATE/feature_request.md.jinja": ".github/ISSUE_TEMPLATE/feature_request.md",
    "template/src/{{ package_name }}/common/bump_version.py.jinja": "src/{{ package_name }}/common/bump_version.py",
}

# Always include these (user customization hotspots even if not in the map above).
BASE_SKIP_ENTRIES: list[str] = [
    "pyproject.toml",
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CLAUDE.md",
    "env.example",
    "src/{{ package_name }}/__init__.py",
    "mkdocs.yml",
    "docs/",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/CODE_OF_CONDUCT.md",
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/feature_request.md",
    "src/{{ package_name }}/common/bump_version.py",
]

# Paths touched at least this often in recent history are added to the skip list.
GIT_FREQUENCY_THRESHOLD = 2
GIT_LOG_LIMIT = 3000


def repo_root() -> Path:
    """Return the repository root (parent of ``scripts/``)."""
    return Path(__file__).resolve().parent.parent


def git_path_change_counts(root: Path) -> dict[str, int]:
    """Count path occurrences in recent ``git log`` output for ``template/``."""
    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "log",
                f"-n{GIT_LOG_LIMIT}",
                "--name-only",
                "--pretty=format:",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:  # pragma: no cover
        return {}  # pragma: no cover
    if proc.returncode != 0:  # pragma: no cover
        return {}  # pragma: no cover
    counts: dict[str, int] = {}
    for line in proc.stdout.splitlines():
        path = line.strip()
        if not path.startswith("template/"):
            continue
        counts[path] = counts.get(path, 0) + 1
    return counts


def compute_desired_entries(root: Path) -> list[str]:
    """Return the sorted unique skip entries that should appear in ``copier.yml``."""
    entries = set(BASE_SKIP_ENTRIES)
    counts = git_path_change_counts(root)
    for tpl_path, skip_entry in TEMPLATE_PATH_TO_SKIP_ENTRY.items():
        full = root / tpl_path
        if not full.is_file():
            continue
        if counts.get(tpl_path, 0) >= GIT_FREQUENCY_THRESHOLD:
            entries.add(skip_entry)

    # Stable, human-friendly order: directories last, then lexical.
    def sort_key(s: str) -> tuple[int, str]:
        is_dir = 0 if s.endswith("/") else 1
        return (is_dir, s.lower())

    return sorted(entries, key=sort_key)


def read_skip_block(text: str) -> tuple[list[str], int, int] | None:
    """Parse ``_skip_if_exists`` list: return entries and [start, end) line indices."""
    lines = text.splitlines(keepends=True)
    start_idx: int | None = None
    for i, line in enumerate(lines):
        if line.startswith("_skip_if_exists:"):
            start_idx = i
            break
    if start_idx is None:
        return None
    end_idx = start_idx + 1
    while end_idx < len(lines) and lines[end_idx].startswith("  - "):
        end_idx += 1
    entries: list[str] = []
    for j in range(start_idx + 1, end_idx):
        line = lines[j]
        if line.startswith("  - "):
            entries.append(line[4:].strip())
    return (entries, start_idx, end_idx)


def replace_skip_block(text: str, entries: list[str]) -> str:
    """Replace the ``_skip_if_exists`` block with ``entries``."""
    parsed = read_skip_block(text)
    if parsed is None:  # pragma: no cover
        raise ValueError("copier.yml: _skip_if_exists block not found")  # pragma: no cover
    _entries, start_idx, end_idx = parsed
    lines = text.splitlines(keepends=True)
    new_middle = [f"  - {item}\n" for item in entries]
    if new_middle:
        new_middle.append("\n")
    return "".join(lines[: start_idx + 1] + new_middle + lines[end_idx:])


def main() -> int:
    """Parse CLI flags and update or verify ``copier.yml``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write copier.yml when the list changes (default: check only, exit 1 if drift).",
    )
    args = parser.parse_args()

    root = repo_root()
    copier_path = root / "copier.yml"
    raw = copier_path.read_text(encoding="utf-8")
    parsed = read_skip_block(raw)
    if parsed is None:  # pragma: no cover
        print("sync_skip_if_exists: could not parse _skip_if_exists in copier.yml", file=sys.stderr)  # pragma: no cover
        return 2  # pragma: no cover
    current, _s, _e = parsed

    desired = compute_desired_entries(root)
    if current == desired:
        print("sync_skip_if_exists: _skip_if_exists is up to date")
        return 0

    print("sync_skip_if_exists: drift detected")
    for label, items in ("current", current), ("desired", desired):
        print(f"  {label}:")
        for item in items:
            print(f"    - {item}")

    if not args.write:
        return 1

    updated = replace_skip_block(raw, desired)
    copier_path.write_text(updated, encoding="utf-8", newline="\n")  # pragma: no cover
    print("sync_skip_if_exists: wrote copier.yml")  # pragma: no cover
    return 0  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

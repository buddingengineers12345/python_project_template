#!/usr/bin/env python3
"""Keep ``_skip_if_exists`` in ``copier.yml`` aligned with template and git.

Synchronizes a curated base list with paths inferred from frequently touched
template sources so user-editable files stay protected on ``copier update``.

See ``.github/workflows/sync-skip-if-exists.yml`` for scheduled automation.

Constants:
    TEMPLATE_PATH_TO_SKIP_ENTRY: Maps template source paths to rendered
        ``_skip_if_exists`` entries (``{{ package_name }}`` preserved).
    BASE_SKIP_ENTRIES: Always-included paths (user customization hotspots).
    GIT_FREQUENCY_THRESHOLD: Minimum occurrences to auto-add a path.
    GIT_LOG_LIMIT: Maximum number of commits scanned for path frequency.
"""

from __future__ import annotations

import argparse
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Map template paths to destination paths for ``_skip_if_exists``. Copier variables
# (``{{ package_name }}``) are preserved for rendered output paths.
TEMPLATE_PATH_TO_SKIP_ENTRY: dict[str, str] = {
    "template/env.example.jinja": "env.example",
    "template/README.md.jinja": "README.md",
    "template/CONTRIBUTING.md.jinja": "CONTRIBUTING.md",
    "template/SECURITY.md.jinja": "SECURITY.md",
    "template/CLAUDE.md.jinja": "CLAUDE.md",
    "template/pyproject.toml.jinja": "pyproject.toml",
    "template/mkdocs.yml.jinja": "mkdocs.yml",
    "template/src/{{ package_name }}/__init__.py.jinja": "src/{{ package_name }}/__init__.py",
    "template/.github/PULL_REQUEST_TEMPLATE.md.jinja":
        ".github/PULL_REQUEST_TEMPLATE.md",
    "template/.github/CODE_OF_CONDUCT.md.jinja":
        ".github/CODE_OF_CONDUCT.md",
    "template/.github/ISSUE_TEMPLATE/bug_report.md.jinja":
        ".github/ISSUE_TEMPLATE/bug_report.md",
    "template/.github/ISSUE_TEMPLATE/feature_request.md.jinja":
        ".github/ISSUE_TEMPLATE/feature_request.md",
    "template/src/{{ package_name }}/common/bump_version.py.jinja":
        "src/{{ package_name }}/common/bump_version.py",
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
    """Return the repository root (parent of the ``scripts/`` directory).

    Returns:
        The absolute path to the repository root.
    """
    return Path(__file__).resolve().parent.parent


def template_path_counts_from_git_log_text(log_stdout: str) -> dict[str, int]:
    """Count ``template/`` path occurrences from ``git log --name-only`` output.

    Blank lines and non-template paths are ignored. Suitable for testing without git.

    Args:
        log_stdout: Output from ``git log --name-only`` style command.

    Returns:
        Dict mapping template paths to their occurrence counts.
    """
    counts: dict[str, int] = {}
    for line in log_stdout.splitlines():
        path = line.strip()
        if path.startswith("template/"):
            counts[path] = counts.get(path, 0) + 1
    return counts


def _git_name_only_log_stdout(root: Path) -> str:
    """Run ``git log`` for recent renames; return stdout or empty string on failure."""
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
    except FileNotFoundError:  # pragma: no cover -- git executable missing on PATH
        return ""
    if proc.returncode != 0:  # pragma: no cover -- invalid git repo or git error in CI
        return ""
    return proc.stdout


def git_path_change_counts(root: Path) -> dict[str, int]:
    """Count path occurrences in recent ``git log`` output for ``template/``."""
    return template_path_counts_from_git_log_text(_git_name_only_log_stdout(root))


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
    if parsed is None:
        raise ValueError("copier.yml: _skip_if_exists block not found")
    _entries, start_idx, end_idx = parsed
    lines = text.splitlines(keepends=True)
    new_middle = [f"  - {item}\n" for item in entries]
    if new_middle:
        new_middle.append("\n")
    return "".join(lines[: start_idx + 1] + new_middle + lines[end_idx:])


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and update or verify the ``_skip_if_exists`` list.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        ``0`` if the skip list is up to date (or updated), ``1`` if changes are
        needed but --write was not provided, ``2`` if an error occurred.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write copier.yml when the list changes (default: check only, exit 1 if drift).",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    copier_path = root / "copier.yml"
    raw = copier_path.read_text(encoding="utf-8")
    parsed = read_skip_block(raw)
    if parsed is None:
        logger.error("could not parse _skip_if_exists in copier.yml")
        return 2
    current, _s, _e = parsed

    desired = compute_desired_entries(root)
    if current == desired:
        logger.info("_skip_if_exists is up to date")
        return 0

    logger.warning("drift detected")
    for label, items in ("current", current), ("desired", desired):
        logger.info(f"{label}:")
        for item in items:
            logger.info(f"  - {item}")

    if not args.write:
        return 1

    updated = replace_skip_block(raw, desired)
    copier_path.write_text(updated, encoding="utf-8", newline="\n")
    logger.info("wrote copier.yml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

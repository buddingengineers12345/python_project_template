#!/usr/bin/env python3
"""Add @pytest.mark.slow to test functions identified as slow.

Reads a JSON array of slow tests (from find_slow_tests.py) and inserts the
@pytest.mark.slow decorator on each function that does not already have it.
Also ensures `import pytest` is present in modified files.

Usage:
    # Pipe from find_slow_tests.py
    python find_slow_tests.py --threshold 1.0 | python mark_slow_tests.py

    # Or from a saved JSON file
    python mark_slow_tests.py --input slow_tests.json

    # Dry-run to preview changes without writing
    python mark_slow_tests.py --input slow_tests.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_LOG = logging.getLogger(__name__)


@dataclass
class PendingMark:
    """A test function that needs the @pytest.mark.slow decorator."""

    file_path: str
    function_name: str
    duration: float


@dataclass
class FileEdit:
    """Tracks all edits to be made to a single file."""

    path: Path
    marks_to_add: list[PendingMark]


def _stripped_lines(lines: list[str]) -> list[str]:
    """Return lines without trailing newlines (for pattern matching)."""
    return [ln.rstrip("\n") for ln in lines]


def find_function_line(lines: list[str], function_name: str) -> int | None:
    """Find the line index of a def statement matching function_name.

    Returns the 0-based line index, or None if not found.
    """
    pattern = re.compile(rf"^\s*(?:async\s+)?def\s+{re.escape(function_name)}\s*\(")
    for i, line in enumerate(lines):
        if pattern.match(line):
            return i
    return None


def already_has_slow_marker(lines: list[str], def_line: int) -> bool:
    """Check whether the lines above a def already include @pytest.mark.slow."""
    # Walk backwards from the def line looking for decorators
    i = def_line - 1
    while i >= 0:
        stripped = lines[i].strip()
        if stripped.startswith("@"):
            if "pytest.mark.slow" in stripped:
                return True
            i -= 1
            continue
        # If we hit a non-decorator, non-blank line, stop
        if stripped and not stripped.startswith("#"):
            break
        i -= 1
    return False


def has_pytest_import(lines: list[str]) -> bool:
    """Check whether the file already imports pytest."""
    for line in lines:
        stripped = line.strip()
        if stripped == "import pytest" or stripped.startswith("from pytest"):
            return True
        if re.match(r"^import\s+pytest\b", stripped):
            return True
    return False


def find_import_insert_line(lines: list[str]) -> int:
    """Find the best line to insert 'import pytest'.

    Inserts after the last stdlib/third-party import block, or at the top of the
    file (after docstrings and comments).
    """
    last_import_line = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            last_import_line = i

    if last_import_line >= 0:
        return last_import_line + 1

    # No imports found — insert after initial comments/docstrings
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith('"""'):
            return i

    return 0


def _plan_decorator_insertions(
    lines: list[str], stripped: list[str], marks_to_add: list[PendingMark], path: Path
) -> tuple[dict[int, str], list[str]]:
    """Compute line-index → decorator text and human-readable change lines."""
    changes: list[str] = []
    insertions: dict[int, str] = {}

    for mark in marks_to_add:
        def_line = find_function_line(stripped, mark.function_name)
        if def_line is None:
            changes.append(f"  SKIP {mark.function_name} in {path} (def not found)")
            continue

        if already_has_slow_marker(stripped, def_line):
            changes.append(f"  SKIP {mark.function_name} in {path} (already marked slow)")
            continue

        indent = re.match(r"^(\s*)", lines[def_line]).group(1)  # type: ignore[union-attr]
        insertions[def_line] = f"{indent}@pytest.mark.slow\n"
        changes.append(
            f"  ADD  @pytest.mark.slow → {mark.function_name} ({mark.duration:.2f}s) in {path}"
        )

    return insertions, changes


def _write_file_with_import_and_decorators(
    path: Path,
    lines: list[str],
    stripped: list[str],
    insertions: dict[int, str],
    dry_run: bool,
) -> list[str]:
    """Build new file content with optional import and decorators; return extra changes."""
    extra: list[str] = []
    needs_import = not has_pytest_import(stripped)
    import_line = find_import_insert_line(stripped) if needs_import else -1

    new_lines: list[str] = []
    import_inserted = False

    for i, line in enumerate(lines):
        if needs_import and i == import_line and not import_inserted:
            new_lines.append("import pytest\n")
            import_inserted = True
            extra.append(f"  ADD  import pytest → {path}")

        if i in insertions:
            new_lines.append(insertions[i])

        new_lines.append(line)

    if not dry_run:
        path.write_text("".join(new_lines), encoding="utf-8")

    return extra


def apply_marks(file_edit: FileEdit, dry_run: bool = False) -> list[str]:
    """Apply @pytest.mark.slow to the identified functions in a file.

    Returns a list of human-readable change descriptions.
    """
    path = file_edit.path
    if not path.exists():
        return [f"  SKIP {path} (file not found)"]

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    stripped = _stripped_lines(lines)

    insertions, changes = _plan_decorator_insertions(lines, stripped, file_edit.marks_to_add, path)

    if not insertions:
        return changes

    extra = _write_file_with_import_and_decorators(path, lines, stripped, insertions, dry_run)
    return changes + extra


def main() -> None:
    """Entry point for mark_slow_tests."""
    parser = argparse.ArgumentParser(description="Add @pytest.mark.slow to slow test functions.")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to JSON file from find_slow_tests.py (default: read stdin)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without modifying files",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr, force=True)

    raw = Path(args.input).read_text(encoding="utf-8") if args.input else sys.stdin.read()

    try:
        slow_tests = json.loads(raw)
    except json.JSONDecodeError as e:
        _LOG.error("Error: could not parse JSON input: %s", e)
        sys.exit(1)

    if not slow_tests:
        _LOG.info("No slow tests to mark.")
        sys.exit(0)

    # Group by file
    file_edits: dict[str, FileEdit] = {}
    for entry in slow_tests:
        fp = entry["file_path"]
        if fp not in file_edits:
            file_edits[fp] = FileEdit(path=Path(fp), marks_to_add=[])
        file_edits[fp].marks_to_add.append(
            PendingMark(
                file_path=fp,
                function_name=entry["function_name"],
                duration=entry["duration"],
            )
        )

    # Apply marks
    all_changes: list[str] = []
    for file_edit in file_edits.values():
        all_changes.extend(apply_marks(file_edit, dry_run=args.dry_run))

    # Report
    mode = "DRY RUN" if args.dry_run else "APPLIED"
    _LOG.info("\n  [%s] @pytest.mark.slow changes:\n\n", mode)
    for change in all_changes:
        _LOG.info("%s", change)
    _LOG.info("")

    added = sum(1 for c in all_changes if c.startswith("  ADD  @pytest"))
    skipped = sum(1 for c in all_changes if c.startswith("  SKIP"))
    _LOG.info("  Summary: %s marker(s) added, %s skipped", added, skipped)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Bump the ``[project].version`` field in the meta-repo ``pyproject.toml``.

Used by ``.github/workflows/release.yml`` and local release flows. Writes the updated file and
prints the new PEP 440 version on stdout (single line, no extra text) for shell substitution.
"""

from __future__ import annotations

import argparse
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, cast

logger = logging.getLogger(__name__)

_VERSION_RE = re.compile(r'^(?P<prefix>\s*version\s*=\s*")(?P<ver>\d+\.\d+\.\d+)(".*)$')

BumpKind = Literal["patch", "minor", "major"]


class _Args(Protocol):
    pyproject: str
    bump: str | None
    new_version: str | None


@dataclass(frozen=True)
class Version:
    """Three-part numeric version (major.minor.patch) used for ``pyproject.toml``."""

    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, s: str) -> Version:
        """Parse a dotted version string.

        Args:
            s: Version string such as ``"1.2.3"``; surrounding whitespace is ignored.

        Returns:
            Parsed :class:`Version` instance.

        Raises:
            ValueError: If ``s`` is not exactly three dot-separated digit groups.
        """
        parts = s.strip().split(".")
        if len(parts) != 3 or any(not p.isdigit() for p in parts):
            raise ValueError(f"Invalid version (expected X.Y.Z): {s!r}")
        return cls(int(parts[0]), int(parts[1]), int(parts[2]))

    def bumped(self, bump: BumpKind) -> Version:
        """Return a new version after a semver-style bump.

        Args:
            bump: ``patch`` increments patch; ``minor`` increments minor and resets patch;
                ``major`` increments major and resets minor and patch.

        Returns:
            New :class:`Version` (this dataclass is frozen).
        """
        if bump == "patch":
            return Version(self.major, self.minor, self.patch + 1)
        if bump == "minor":
            return Version(self.major, self.minor + 1, 0)
        return Version(self.major + 1, 0, 0)

    def __str__(self) -> str:
        """Return ``major.minor.patch`` as a dotted string."""
        return f"{self.major}.{self.minor}.{self.patch}"


def _read_project_version(pyproject_path: Path) -> Version:
    r"""Read ``version = "X.Y.Z"`` from the first ``[project]`` table."""
    text = pyproject_path.read_text(encoding="utf-8")
    in_project = False
    for line in text.splitlines():
        if line.strip() == "[project]":
            in_project = True
            continue
        if in_project and line.startswith("[") and line.strip().endswith("]"):
            break
        if in_project:
            m = _VERSION_RE.match(line)
            if m:
                return Version.parse(m.group("ver"))
    msg = f'Could not find [project] version line (version = "X.Y.Z") in {pyproject_path}'
    raise RuntimeError(msg)


def _write_project_version(pyproject_path: Path, new_version: Version) -> None:
    """Replace the version line inside ``[project]`` only."""
    text = pyproject_path.read_text(encoding="utf-8")
    out_lines: list[str] = []
    in_project = False
    replaced = False

    for line in text.splitlines():
        if line.strip() == "[project]":
            in_project = True
            out_lines.append(line)
            continue
        if in_project and line.startswith("[") and line.strip().endswith("]"):
            in_project = False
        if in_project:
            m = _VERSION_RE.match(line)
            if m:
                out_lines.append(f"{m.group('prefix')}{new_version}{m.group(3)}")
                replaced = True
                continue
        out_lines.append(line)

    if not replaced:
        msg = f"Could not replace [project] version line in {pyproject_path}"
        raise RuntimeError(msg)

    _ = pyproject_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")


def _parse_args(argv: list[str] | None = None) -> _Args:
    parser = argparse.ArgumentParser(
        description="Bump [project].version in pyproject.toml and print the new version on stdout.",
    )
    _ = parser.add_argument(
        "--pyproject",
        default="pyproject.toml",
        metavar="PATH",
        help="Path to pyproject.toml (default: pyproject.toml in cwd).",
    )
    _ = parser.add_argument(
        "--bump",
        choices=("patch", "minor", "major"),
        help="Which semver part to bump (ignored if --new-version is set).",
    )
    _ = parser.add_argument(
        "--new-version",
        metavar="X.Y.Z",
        help="Set an explicit three-part version (overrides --bump).",
    )
    return cast("_Args", cast("object", parser.parse_args(argv)))


def main(argv: list[str] | None = None) -> int:
    """Run the CLI: bump ``pyproject.toml`` and print the new version on stdout.

    Returns:
        ``0`` on success.

    Raises:
        SystemExit: If arguments are invalid, the version is unchanged, or I/O fails.
    """
    args = _parse_args(argv)
    pyproject_path = Path(args.pyproject)

    try:
        current = _read_project_version(pyproject_path)
    except OSError as exc:
        raise SystemExit(f"bump_version: cannot read {pyproject_path}: {exc}") from exc
    except RuntimeError as exc:
        raise SystemExit(f"bump_version: {exc}") from exc

    if args.new_version is not None:
        try:
            new = Version.parse(args.new_version)
        except ValueError as exc:
            raise SystemExit(f"bump_version: {exc}") from exc
    else:
        if not args.bump:
            raise SystemExit(
                "bump_version: specify --bump (patch|minor|major) or --new-version X.Y.Z",
            )
        new = current.bumped(cast("BumpKind", args.bump))

    if new == current:
        raise SystemExit(f"bump_version: new version equals current ({current}); nothing to do")

    try:
        _write_project_version(pyproject_path, new)
    except OSError as exc:
        raise SystemExit(f"bump_version: cannot write {pyproject_path}: {exc}") from exc
    except RuntimeError as exc:
        raise SystemExit(f"bump_version: {exc}") from exc

    logger.info(str(new))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

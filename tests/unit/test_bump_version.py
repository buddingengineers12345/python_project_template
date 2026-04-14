"""Tests for ``scripts/bump_version`` (PEP 440 bumps and ``pyproject.toml`` I/O)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Literal, cast

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_SCRIPT = REPO_ROOT / "scripts" / "bump_version.py"
_SPEC = importlib.util.spec_from_file_location("bump_version", _SCRIPT)
assert _SPEC is not None
assert _SPEC.loader is not None
_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["bump_version"] = _mod
_SPEC.loader.exec_module(_mod)
bv = _mod


def test_version_parse_accepts_simple_triplet() -> None:
    """Parse a standard ``X.Y.Z`` string into components."""
    v = bv.Version.parse("  2.10.3  ")
    assert v.major == 2
    assert v.minor == 10
    assert v.patch == 3


def test_version_parse_rejects_invalid() -> None:
    """Non-numeric or wrong segment counts raise ``ValueError``."""
    with pytest.raises(ValueError, match=r"X\.Y\.Z"):
        bv.Version.parse("1.2")
    with pytest.raises(ValueError, match=r"X\.Y\.Z"):
        bv.Version.parse("a.b.c")


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("patch", (1, 2, 4)),
        ("minor", (1, 3, 0)),
        ("major", (2, 0, 0)),
    ],
)
def test_version_bumped(kind: str, expected: tuple[int, int, int]) -> None:
    """``bumped`` applies patch, minor, or major semantics."""
    base = bv.Version(1, 2, 3)
    out = base.bumped(cast("Literal['patch', 'minor', 'major']", kind))
    assert (out.major, out.minor, out.patch) == expected


def test_read_and_write_project_version_roundtrip(tmp_path: Path) -> None:
    """Read version from a minimal ``pyproject.toml`` and write a new one back."""
    path = tmp_path / "pyproject.toml"
    path.write_text(
        '[project]\nname = "x"\nversion = "0.1.0"\n\n[tool.x]\nkey = "v"\n',
        encoding="utf-8",
    )
    assert bv._read_project_version(path) == bv.Version(0, 1, 0)
    bv._write_project_version(path, bv.Version(0, 1, 1))
    assert bv._read_project_version(path) == bv.Version(0, 1, 1)


def test_cli_new_version_prints_and_updates(tmp_path: Path) -> None:
    """``--new-version`` updates the file and prints the version on stdout."""
    import contextlib
    import io as _io

    path = tmp_path / "pyproject.toml"
    path.write_text('[project]\nname = "x"\nversion = "1.0.0"\n', encoding="utf-8")
    buf = _io.StringIO()
    saved_argv = sys.argv
    try:
        sys.argv = [str(_SCRIPT), "--pyproject", str(path), "--new-version", "1.0.1"]
        with contextlib.redirect_stdout(buf):
            rc = bv.main()
    finally:
        sys.argv = saved_argv
    assert rc == 0
    assert buf.getvalue().strip() == "1.0.1"
    assert 'version = "1.0.1"' in path.read_text(encoding="utf-8")


def test_cli_bump_patch_increments_patch(tmp_path: Path) -> None:
    """``--bump patch`` increments the patch component and prints the new version."""
    import contextlib
    import io as _io

    path = tmp_path / "pyproject.toml"
    path.write_text('[project]\nname = "x"\nversion = "2.3.4"\n', encoding="utf-8")
    buf = _io.StringIO()
    saved_argv = sys.argv
    try:
        sys.argv = [str(_SCRIPT), "--pyproject", str(path), "--bump", "patch"]
        with contextlib.redirect_stdout(buf):
            rc = bv.main()
    finally:
        sys.argv = saved_argv
    assert rc == 0
    assert buf.getvalue().strip() == "2.3.5"

"""Tests for ``scripts/sync_skip_if_exists`` (``_skip_if_exists`` parsing and updates)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_SCRIPT = REPO_ROOT / "scripts" / "sync_skip_if_exists.py"
_SPEC = importlib.util.spec_from_file_location("sync_skip_if_exists", _SCRIPT)
assert _SPEC is not None
assert _SPEC.loader is not None
_mod = importlib.util.module_from_spec(_SPEC)
sys.modules["sync_skip_if_exists"] = _mod
_SPEC.loader.exec_module(_mod)
ssi = _mod


def test_read_skip_block_extracts_entries() -> None:
    """Parse YAML lines under ``_skip_if_exists`` into ordered entries."""
    text = """_skip_if_exists:
  - foo
  - bar

_other: true
"""
    parsed = ssi.read_skip_block(text)
    assert parsed is not None
    entries, start, end = parsed
    assert entries == ["foo", "bar"]
    assert start == 0
    assert end == 3


def test_read_skip_block_missing_returns_none() -> None:
    """When the key is absent, return ``None``."""
    assert ssi.read_skip_block("name: x\n") is None


def test_replace_skip_block_rewrites_list() -> None:
    """Replace the list while preserving surrounding content."""
    text = """top: true
_skip_if_exists:
  - old

tail: end
"""
    out = ssi.replace_skip_block(text, ["a", "b"])
    assert "_skip_if_exists:\n" in out
    assert "  - a\n" in out
    assert "  - b\n" in out
    assert "old" not in out
    assert "top: true" in out
    assert "tail: end" in out


def test_compute_desired_entries_includes_base(tmp_path: Path) -> None:
    """``BASE_SKIP_ENTRIES`` are always part of the desired set."""
    # Minimal repo layout: only copier.yml is not required for compute_desired_entries
    root = tmp_path
    desired = set(ssi.compute_desired_entries(root))
    for item in ssi.BASE_SKIP_ENTRIES:
        assert item in desired


def test_repo_root_points_at_workspace_parent() -> None:
    """``repo_root`` resolves to the directory containing ``scripts/``."""
    assert ssi.repo_root() == REPO_ROOT


def test_main_check_mode_runs_without_error() -> None:
    """``main()`` in check-only mode (no ``--write``) completes and returns an int."""
    import contextlib
    import io

    buf = io.StringIO()
    saved_argv = sys.argv
    try:
        sys.argv = [str(_SCRIPT)]
        with contextlib.redirect_stdout(buf):
            rc = ssi.main()
    finally:
        sys.argv = saved_argv
    assert rc in {0, 1}  # 0 = up to date; 1 = drift detected (both are valid outcomes)

"""Tests for ``scripts/sync_skip_if_exists`` (``_skip_if_exists`` parsing and updates)."""

from __future__ import annotations

import sys
from pathlib import Path  # noqa: TC003

import pytest
from tests.script_imports import REPO_ROOT, load_script_module

_SCRIPT = REPO_ROOT / "scripts" / "sync_skip_if_exists.py"
ssi = load_script_module("sync_skip_if_exists")


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


def test_replace_skip_block_raises_when_block_missing() -> None:
    """``replace_skip_block`` requires an existing ``_skip_if_exists`` key."""
    with pytest.raises(ValueError, match="_skip_if_exists"):
        ssi.replace_skip_block("project_name: x\n", ["a"])


def test_template_path_counts_from_git_log_text() -> None:
    """Only ``template/`` paths are counted; blank lines ignored."""
    text = "\n template/a.jinja \nfoo\n  template/b.jinja  \ntemplate/a.jinja\n"
    counts = ssi.template_path_counts_from_git_log_text(text)
    assert counts["template/a.jinja"] == 2
    assert counts["template/b.jinja"] == 1


def test_main_write_resyncs_copier_yml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """``--write`` rewrites ``copier.yml`` so ``_skip_if_exists`` matches desired entries."""
    monkeypatch.setattr(ssi, "repo_root", lambda: tmp_path)
    desired = ssi.compute_desired_entries(tmp_path)
    (tmp_path / "copier.yml").write_text(
        "_skip_if_exists:\n  - definitely-not-in-desired-list\n\nx: 1\n",
        encoding="utf-8",
    )
    rc = ssi.main(["--write"])
    assert rc == 0
    new_raw = (tmp_path / "copier.yml").read_text(encoding="utf-8")
    parsed = ssi.read_skip_block(new_raw)
    assert parsed is not None
    assert parsed[0] == desired
    assert "x: 1" in new_raw

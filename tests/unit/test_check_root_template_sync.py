"""CLI smoke tests for ``scripts/check_root_template_sync``.

Detailed policy scenarios are in ``tests/unit/test_root_template_sync.py``.
"""

from __future__ import annotations

import contextlib
import io
import sys

from tests.script_imports import REPO_ROOT, load_script_module

_SCRIPT = REPO_ROOT / "scripts" / "check_root_template_sync.py"
crs = load_script_module("check_root_template_sync")


def test_check_root_template_sync_help_exits_zero() -> None:
    """The script exposes argparse ``--help`` and exits successfully."""
    buf = io.StringIO()
    saved_argv = sys.argv
    try:
        sys.argv = [str(_SCRIPT), "--help"]
        with contextlib.redirect_stdout(buf):
            try:
                crs.main()
                returncode = 0
            except SystemExit as exc:
                returncode = int(exc.code) if exc.code is not None else 0
    finally:
        sys.argv = saved_argv

    assert returncode == 0
    assert "sync" in buf.getvalue().lower()

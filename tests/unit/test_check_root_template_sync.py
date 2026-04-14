"""CLI smoke tests for ``scripts/check_root_template_sync``.

Detailed policy scenarios are in ``tests/unit/test_root_template_sync.py``.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_SCRIPT = REPO_ROOT / "scripts" / "check_root_template_sync.py"
_SPEC = importlib.util.spec_from_file_location("check_root_template_sync", _SCRIPT)
assert _SPEC is not None
assert _SPEC.loader is not None
_crs = sys.modules.get("check_root_template_sync")
if _crs is None:
    _crs = importlib.util.module_from_spec(_SPEC)
    sys.modules["check_root_template_sync"] = _crs
    assert _SPEC.loader is not None
    _SPEC.loader.exec_module(_crs)
crs = _crs


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

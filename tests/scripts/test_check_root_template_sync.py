"""CLI smoke tests for ``scripts/check_root_template_sync``.

Detailed policy scenarios are in ``tests/scripts/test_root_template_sync.py``.
"""

from __future__ import annotations

import subprocess
import sys

from tests._paths import REPO_ROOT

_SCRIPT = REPO_ROOT / "scripts" / "check_root_template_sync.py"


def test_check_root_template_sync_help_exits_zero() -> None:
    """The script exposes argparse ``--help`` and exits successfully."""
    proc = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "Check root/template sync" in proc.stdout or "sync" in proc.stdout.lower()

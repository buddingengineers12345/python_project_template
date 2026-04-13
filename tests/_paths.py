"""Path constants for the Copier meta-repo test suite."""

from __future__ import annotations

from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = _TESTS_DIR.parent
TEMPLATE_ROOT = REPO_ROOT / "template"
COPIER_YAML = REPO_ROOT / "copier.yml"

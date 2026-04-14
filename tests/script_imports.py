"""Load top-level ``scripts/*.py`` files as importable modules for unit tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_script_module(stem: str):
    """Load ``scripts/<stem>.py`` under the module name ``stem`` (cached in ``sys.modules``)."""
    script_path = REPO_ROOT / "scripts" / f"{stem}.py"
    existing = sys.modules.get(stem)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(stem, script_path)
    if spec is None or spec.loader is None:
        msg = f"cannot load script module {stem!r} from {script_path}"
        raise RuntimeError(msg)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[stem] = mod
    spec.loader.exec_module(mod)
    return mod

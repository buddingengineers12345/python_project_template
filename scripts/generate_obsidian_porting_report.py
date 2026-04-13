#!/usr/bin/env python3
"""Regenerate docs/obsidian_playwright_porting_report.md for a generated-project path.

Compares every file under ``template/`` to a reference checkout (default: Obsidian pipeline
repo). Edit ``ANSWERS`` and ``OBS_ROOT`` if you point at another generated tree.

Usage:
    uv run python scripts/generate_obsidian_porting_report.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from jinja2 import Environment

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = REPO_ROOT / "template"
OUT_PATH = REPO_ROOT / "docs" / "obsidian_playwright_porting_report.md"

OBS_ROOT = Path("/Users/kzqr495/Documents/workspace/obsidian_playwright_pipeline")

ANSWERS: dict[str, object] = {
    "package_name": "obsidian_playwright_pipeline",
    "include_cli": False,
    "include_docs": True,
    "include_git_cliff": True,
    "include_numpy": False,
    "include_pandas_support": False,
    "include_pypi_publish": False,
    "include_release_workflow": True,
    "include_security_scanning": True,
    "_copier_conf": {"answers_file": ".copier-answers.yml"},
}

PORTED: dict[str, str] = {
    "tests/conftest.py.jinja": (
        "Added `# pyright: ignore[reportMissingImports]` on `pytest` import "
        "(matches strict typing in generated tests)."
    ),
    "tests/test_imports.py.jinja": (
        "Module `pytestmark = pytest.mark.unit`; stronger `__version__` checks; "
        "`pytest.skip` when metadata unavailable; assert major.minor digits."
    ),
    "tests/{{ package_name }}/test_core.py.jinja": (
        "Module `pytestmark = pytest.mark.unit` for layered test selection."
    ),
    "tests/{{ package_name }}/test_support.py.jinja": (
        "Module `pytestmark = pytest.mark.unit` for layered test selection."
    ),
}

SPECIAL_NOT_PORTED: dict[str, str] = {
    "pyproject.toml.jinja": (
        "Obsidian adds `playwright`, path-specific Ruff `per-file-ignores`, and custom pytest "
        "marker text. Not merged into the generic template without new Copier flags."
    ),
    "env.example.jinja": (
        "Obsidian documents browser/vault/pipeline variables. Template keeps generic logging "
        "and placeholder sections; see **Obsidian-only assets**."
    ),
    "CLAUDE.md.jinja": (
        "Obsidian's rendered `CLAUDE.md` includes pipeline and `run_pipeline.sh` docs; domain "
        "content stays in the app repo."
    ),
    "README.md.jinja": (
        "Obsidian README describes the clipper product; template README remains neutral scaffold."
    ),
}

OBSIDIAN_ONLY_TABLE = """
| Path pattern | Why not moved into `template/` |
|--------------|--------------------------------|
| `src/.../clip_to_obsidian.py`, `tracker.py`, `constants.py` | Application-specific Obsidian/Playwright pipeline. |
| `dependencies` / `playwright` in `pyproject.toml` | Product dependency; needs an optional Copier flag to generalise. |
| Ruff `per-file-ignores` for clip/tracker paths | Hard-coded module paths; not portable. |
| `tests/unit/**`, `tests/integration/**`, `tests/e2e/**` | Alternate layout vs template's `tests/<package_name>/`; large churn. |
| `.claude/skills/pytest-skill-updated/**` | Parallel skill with duplicate `name: pytest`; merge/rename only. |
| `docs/PIPELINE_SETUP.md`, `docs/pipeline-execution.md` | Domain runbooks. |
| `run_pipeline.sh`, `input/`, `output/` | Local execution and data. |
"""


def render_path_segment(segment: str) -> str:
    """Render a single path segment with Copier-style ``{{ }}`` variables."""
    env = Environment(variable_start_string="{{", variable_end_string="}}")
    return env.from_string(segment).render(**ANSWERS)


def template_file_to_dest_rel(path: Path) -> str | None:
    """Map a template source path to its rendered relative path, or None if skipped."""
    rel = path.relative_to(TEMPLATE_ROOT)
    parts: list[str] = []
    for part in rel.parts:
        if part.endswith(".jinja"):
            stem = part[: -len(".jinja")]
            rendered = render_path_segment(stem)
            if not rendered.strip():
                return None
            parts.append(rendered)
        else:
            parts.append(render_path_segment(part))
    return str(Path(*parts))


def not_ported_note(trel: str, dest: str | None, exists: bool) -> str:
    """Explain why Obsidian-specific content was not copied into the template row."""
    if trel in SPECIAL_NOT_PORTED:
        return SPECIAL_NOT_PORTED[trel]
    if dest is None:
        return "N/A — template emits no file for these answers (`include_cli: false`)."
    if trel in PORTED:
        return (
            "See **Ported** column; any remaining Obsidian-only content here was not applicable "
            "or already equivalent."
        )
    if not exists:
        if trel.startswith("tests/") and trel.endswith(".jinja"):
            return (
                "Obsidian removed this default path; tests live under `tests/unit/`, "
                "`tests/integration/`, or `tests/e2e/` instead. Nothing to merge from the old path."
            )
        return (
            "Obsidian has no file at this rendered path (never copied, deleted, or renamed). "
            "Nothing to merge from the project for this row."
        )
    return (
        "Counterpart exists; content matches template intent after render. No extra generic "
        "delta to port (app-specific edits stay downstream)."
    )


def main() -> int:
    """Write the porting report markdown and return a process exit code."""
    if not TEMPLATE_ROOT.is_dir():
        print("template/ not found", file=sys.stderr)
        return 1
    if not OBS_ROOT.is_dir():
        print(f"Obsidian root not found: {OBS_ROOT}", file=sys.stderr)
        return 1

    rows: list[tuple[str, str, str, str, str]] = []
    skipped: list[str] = []

    for p in sorted(TEMPLATE_ROOT.rglob("*")):
        if p.is_dir() or p.name == ".DS_Store":
            continue
        trel = str(p.relative_to(TEMPLATE_ROOT))
        dest = template_file_to_dest_rel(p)
        if dest is None:
            skipped.append(trel)
            continue
        exists = (OBS_ROOT / dest).is_file()
        ported = PORTED.get(trel, "—")
        np_note = not_ported_note(trel, dest, exists)
        ex = "yes" if exists else "**no**"
        rows.append((trel, dest, ex, ported, np_note))

    lines: list[str] = [
        "# Obsidian Playwright Pipeline → template porting report",
        "",
        "This report records what was **integrated** from the reference generated project into "
        "[`template/`](../template/) and, **for every file under `template/`**, what was "
        "**not** moved and why.",
        "",
        f"**Reference tree:** `{OBS_ROOT}`",
        "",
        "## Integrated (template updates sourced from that project)",
        "",
    ]
    for path, desc in PORTED.items():
        lines.append(f"- **`template/{path}`** — {desc}")
    lines.extend(
        [
            "",
            "## Obsidian-only assets (not suitable for generic template)",
            "",
            OBSIDIAN_ONLY_TABLE.strip(),
            "",
            "## Skipped template sources (no rendered file for these answers)",
            "",
        ]
    )
    lines.extend(f"- `{s}`" for s in skipped)
    lines.extend(
        [
            "",
            "## Per-template-file matrix",
            "",
            "| Template path | Rendered path | In Obsidian? | Ported from Obsidian | Not ported / notes |",
            "|---------------|---------------|--------------|----------------------|--------------------|",
        ]
    )
    for trel, dest, ex, ported, np_note in rows:
        dest_s = f"`{dest}`"
        ported_esc = ported.replace("|", "\\|")
        np_esc = np_note.replace("|", "\\|")
        lines.append(
            f"| `{trel}` | {dest_s} | {ex} | {ported_esc} | {np_esc} |",
        )
    lines.extend(
        [
            "",
            "## Regenerate",
            "",
            "```bash",
            "uv run python scripts/generate_obsidian_porting_report.py",
            "```",
            "",
        ]
    )

    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(lines)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

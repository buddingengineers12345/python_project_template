#!/usr/bin/env python3
"""Regenerate ``docs/template_vs_obsidian_playwright_pipeline.md``.

Maps each ``template/`` file to its rendered path (Obsidian Copier answers), checks whether
that file exists in the reference project, and whether **text content matches** a fresh
``copier copy`` render (newline-normalised UTF-8).

Edit ``OBS_ROOT`` if you compare against another generated tree.

Usage:
    uv run python scripts/generate_template_vs_obsidian_comparison.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from jinja2 import Environment

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = REPO_ROOT / "template"
OUT_PATH = REPO_ROOT / "docs" / "template_vs_obsidian_playwright_pipeline.md"

OBS_ROOT = Path("/Users/kzqr495/Documents/workspace/obsidian_playwright_pipeline")


def load_copier_data_file(answers_path: Path) -> dict[str, object]:
    """Load consumer answers; drop keys starting with ``_`` for ``copier copy --data-file``."""
    raw = yaml.safe_load(answers_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        msg = "Answers file must be a mapping at top level"
        raise TypeError(msg)
    return {k: v for k, v in raw.items() if not str(k).startswith("_")}


def render_path_segment(segment: str, answers: dict[str, object]) -> str:
    """Render a path segment that may contain ``{{ package_name }}`` etc."""
    env = Environment(variable_start_string="{{", variable_end_string="}}")
    return env.from_string(segment).render(**answers)


def template_file_to_dest_rel(path: Path, answers: dict[str, object]) -> str | None:
    """Map a template source path to its rendered relative path, or None if skipped."""
    rel = path.relative_to(TEMPLATE_ROOT)
    parts: list[str] = []
    for part in rel.parts:
        if part.endswith(".jinja"):
            stem = part[: -len(".jinja")]
            rendered = render_path_segment(stem, answers)
            if not rendered.strip():
                return None
            parts.append(rendered)
        else:
            parts.append(render_path_segment(part, answers))
    return str(Path(*parts))


def run_fresh_copier_render(data: dict[str, object], dest: Path) -> None:
    """Run ``copier copy`` into ``dest`` using the given answer mapping."""
    dest.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yml",
        encoding="utf-8",
        delete=False,
    ) as tmp:
        yaml.safe_dump(data, tmp, default_flow_style=False, sort_keys=True)
        data_path = Path(tmp.name)
    try:
        cmd = [
            "copier",
            "copy",
            "--vcs-ref",
            "HEAD",
            str(REPO_ROOT),
            str(dest),
            "--trust",
            "--defaults",
            "--skip-tasks",
            "--data-file",
            str(data_path),
            "-q",
        ]
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=REPO_ROOT)
        if proc.returncode != 0:
            print(proc.stderr or proc.stdout, file=sys.stderr)
            msg = f"copier copy failed with exit {proc.returncode}"
            raise RuntimeError(msg)
    finally:
        data_path.unlink(missing_ok=True)


def read_normalized_text(path: Path) -> str:
    """Read UTF-8 text with CRLF/CR normalised to LF."""
    text = path.read_text(encoding="utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def content_matches_fresh_render(
    rendered_path: str,
    obsidian_file: Path,
    fresh_root: Path,
) -> str:
    """Return ``yes`` / ``no`` / ``N/A`` for the content-match column."""
    fresh_file = fresh_root / rendered_path
    if not obsidian_file.is_file():
        return "N/A"
    if not fresh_file.is_file():
        return "N/A"
    try:
        a = read_normalized_text(fresh_file)
        b = read_normalized_text(obsidian_file)
    except OSError:
        return "N/A"
    return "yes" if a == b else "no"


def build_markdown(
    data: dict[str, object],
    rows: list[tuple[str, str, str, str, str, str]],
    skipped: list[str],
) -> str:
    """Assemble the full markdown document."""
    present = sum(1 for r in rows if r[3] == "yes")
    absent = sum(1 for r in rows if r[3] == "**no**")
    identical = sum(1 for r in rows if r[4] == "yes")
    differ = sum(1 for r in rows if r[4] == "no")
    na_match = sum(1 for r in rows if r[4] == "N/A")

    answer_lines = [f"| `{key}` | `{data[key]}` |" for key in sorted(data.keys())]
    missing_lines = [
        f"- `{trel}` → `{dest}`" for _k, trel, dest, ex, _m, _n in rows if ex == "**no**"
    ]
    table_lines = [
        f"| {kind} | `{trel}` | `{dest}` | {ex} | **{match}** | {note} |"
        for kind, trel, dest, ex, match, note in rows
    ]
    skip_lines = [f"- `{s}` (`include_cli: false` → no `cli.py`)." for s in skipped]

    lines: list[str] = [
        "# Template vs `obsidian_playwright_pipeline` file comparison",
        "",
        "This document lists every file under [`template/`](../template/), maps it to the path "
        "Copier would emit using the reference project's [`.copier-answers.yml`](file://"
        f"{OBS_ROOT}/.copier-answers.yml), checks whether that path exists in `"
        f"{OBS_ROOT}` today, and whether **file text matches** a **fresh** render from this "
        "repository (`copier copy --vcs-ref HEAD --skip-tasks` with the same answers).",
        "",
        "Content comparison normalises newlines (CRLF → LF). Binary files are not supported; "
        "treat unexpected decode failures as **N/A**.",
        "",
        "## Copier answers (path rendering)",
        "",
        "| Key | Value |",
        "|-----|-------|",
        *answer_lines,
        "| `_copier_conf.answers_file` | `.copier-answers.yml` |",
        "",
        "## Summary",
        "",
        f"- **Template files mapped:** {len(rows)} (plus {len(skipped)} skipped for these answers)",
        f"- **Expected path exists in reference project:** {present}",
        f"- **Expected path missing:** {absent}",
        f"- **Content matches fresh render:** {identical}",
        f"- **Content differs from fresh render:** {differ}",
        f"- **Content match N/A** (missing path or render): {na_match}",
        "",
        "If **Content match** is **no**, the reference project has drifted from the current "
        "template (local edits, template updates since `_commit`, or refactored paths).",
        "",
        "### Missing expected paths (template → would emit → not found)",
        "",
        *missing_lines,
        "",
        "## Skipped template files (no output for these answers)",
        "",
        *skip_lines,
        "",
        "## Full table (all `template/` files)",
        "",
        "| Kind | Template path | Expected path | Exists | Content match | Notes |",
        "|------|---------------|---------------|--------|---------------|-------|",
        *table_lines,
        "",
        "## Regenerate",
        "",
        "```bash",
        "uv run python scripts/generate_template_vs_obsidian_comparison.py",
        "```",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    """Write the comparison markdown."""
    if not TEMPLATE_ROOT.is_dir():
        print("template/ not found", file=sys.stderr)
        return 1
    if not OBS_ROOT.is_dir():
        print(f"Reference project not found: {OBS_ROOT}", file=sys.stderr)
        return 1
    answers_path = OBS_ROOT / ".copier-answers.yml"
    if not answers_path.is_file():
        print(f"Missing {answers_path}", file=sys.stderr)
        return 1

    data = load_copier_data_file(answers_path)
    path_ctx: dict[str, object] = {**data, "_copier_conf": {"answers_file": ".copier-answers.yml"}}

    with tempfile.TemporaryDirectory() as tmp:
        fresh_root = Path(tmp) / "rendered"
        run_fresh_copier_render(data, fresh_root)

        rows: list[tuple[str, str, str, str, str, str]] = []
        skipped: list[str] = []
        for p in sorted(TEMPLATE_ROOT.rglob("*")):
            if p.is_dir() or p.name == ".DS_Store":
                continue
            trel = str(p.relative_to(TEMPLATE_ROOT))
            dest = template_file_to_dest_rel(p, path_ctx)
            if dest is None:
                skipped.append(trel)
                continue
            kind = "Jinja" if trel.endswith(".jinja") else "static"
            obs_file = OBS_ROOT / dest
            exists = obs_file.is_file()
            ex = "yes" if exists else "**no**"
            match = content_matches_fresh_render(dest, obs_file, fresh_root)
            note = (
                "—"
                if kind == "static"
                else "Rendered from `.jinja`; match uses fresh `copier copy`."
            )
            rows.append((kind, trel, dest, ex, match, note))

    text = build_markdown(data, rows, skipped)
    OUT_PATH.write_text(text, encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

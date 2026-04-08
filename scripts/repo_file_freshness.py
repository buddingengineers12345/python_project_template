#!/usr/bin/env python3
"""Generate repository file freshness reports using Git history.

This script:
- Lists only Git-tracked files (via ``git ls-files``).
- Computes each file's last update timestamp (via ``git log -1``).
- Classifies files into green/yellow/red/blue using age thresholds and an ignore config.
- Writes:
  - ``docs/repo_file_status_report.md`` (dashboard)
  - ``file_freshness.json`` (per-file details)
  - ``freshness_summary.json`` (counts + optional badge metadata)

Design notes:
- Git is the source of truth (no filesystem mtimes).
- A single file failing Git history lookup must not fail the whole run.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Literal, Protocol, cast

Status = Literal["green", "yellow", "red", "blue"]


class _Args(Protocol):
    repo_root: str
    ignore_config: str
    output_markdown: str
    output_details_json: str
    output_summary_json: str


@dataclass(frozen=True)
class IgnoreConfig:
    """Ignore configuration loaded from ``freshness_ignore.json``."""

    files: frozenset[str]
    directories: tuple[str, ...]
    extensions: frozenset[str]
    patterns: tuple[str, ...]

    @classmethod
    def empty(cls) -> IgnoreConfig:
        return cls(files=frozenset(), directories=tuple(), extensions=frozenset(), patterns=tuple())


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _now_utc_from_env() -> datetime:
    """Return a deterministic 'now' when FRESHNESS_NOW_ISO is set (for tests)."""
    raw = os.environ.get("FRESHNESS_NOW_ISO")
    if not raw:
        return _now_utc()
    dt = _parse_git_iso_datetime(raw)
    if dt is None:
        print(
            f"[freshness] Warning: invalid FRESHNESS_NOW_ISO (expected ISO-8601): {raw!r}",
            file=sys.stderr,
        )
        return _now_utc()
    return dt


def _run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str] | None:
    """Run a git command, returning the process or None if git is missing."""
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None


def _resolve_repo_root(user_repo_root: str) -> Path:
    """Resolve repository root, falling back to the provided path."""
    candidate = Path(user_repo_root).resolve()
    proc = _run_git(candidate, ["rev-parse", "--show-toplevel"])
    if proc is None or proc.returncode != 0:
        return candidate
    return Path(proc.stdout.strip()).resolve()


def _git_ls_files(root: Path) -> list[str]:
    """Return git-tracked files as POSIX-relative paths."""
    proc = _run_git(root, ["ls-files"])
    if proc is None or proc.returncode != 0:
        return []
    paths = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    # Normalize to POSIX-style even on Windows runners (Git returns / already, but keep consistent).
    return [p.replace("\\", "/") for p in paths]


def _git_last_commit_iso(root: Path, rel_path: str) -> str | None:
    """Return last commit timestamp for a file as an ISO-8601 string, or None."""
    proc = _run_git(root, ["log", "-1", "--format=%cI", "--", rel_path])
    if proc is None or proc.returncode != 0:
        return None
    value = proc.stdout.strip()
    return value or None


def _parse_git_iso_datetime(value: str) -> datetime | None:
    """Parse Git's ISO timestamp (e.g. 2026-04-08T12:34:56+00:00)."""
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        # Defensive: treat naive as UTC.
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _age_days(now: datetime, commit_iso: str | None) -> int | None:
    if commit_iso is None:
        return None
    dt = _parse_git_iso_datetime(commit_iso)
    if dt is None:
        return None
    delta = now - dt
    # Floor to integer days.
    return max(0, int(delta.total_seconds() // 86400))


def _normalize_dir_prefix(s: str) -> str:
    s2 = s.strip().replace("\\", "/")
    if not s2:
        return ""
    if not s2.endswith("/"):
        s2 += "/"
    return s2


def _normalize_extension(s: str) -> str:
    s2 = s.strip().lower()
    if not s2:
        return ""
    if not s2.startswith("."):
        s2 = "." + s2
    return s2


def load_ignore_config(path: Path) -> IgnoreConfig:
    """Load ignore configuration from JSON, falling back to empty on errors."""
    if not path.is_file():
        return IgnoreConfig.empty()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[freshness] Warning: failed to read {path}: {exc}", file=sys.stderr)
        return IgnoreConfig.empty()
    if not isinstance(raw, dict):
        print(f"[freshness] Warning: ignore config root must be an object: {path}", file=sys.stderr)
        return IgnoreConfig.empty()

    def get_list(key: str) -> list[str]:
        v = raw.get(key, [])
        if isinstance(v, list) and all(isinstance(x, str) for x in v):
            return cast(list[str], v)
        print(f"[freshness] Warning: ignore key {key!r} must be a list[str]: {path}", file=sys.stderr)
        return []

    files = frozenset(x.strip().replace("\\", "/") for x in get_list("files") if x.strip())
    directories = tuple(
        d for d in (_normalize_dir_prefix(x) for x in get_list("directories")) if d
    )
    extensions = frozenset(
        e for e in (_normalize_extension(x) for x in get_list("extensions")) if e
    )
    patterns = tuple(x.strip().replace("\\", "/") for x in get_list("patterns") if x.strip())

    # Keep deterministic ordering for tuple fields.
    return IgnoreConfig(
        files=files,
        directories=tuple(sorted(set(directories), key=str.lower)),
        extensions=extensions,
        patterns=tuple(sorted(set(patterns), key=str.lower)),
    )


def ignored_status(rel_path: str, ignore: IgnoreConfig) -> bool:
    """Return True if the path should be ignored (blue), per ignore priority."""
    p = rel_path.replace("\\", "/")

    # 1) Exact file match
    if p in ignore.files:
        return True

    # 2) Directory prefix match
    for d in ignore.directories:
        if p.startswith(d):
            return True

    # 3) Extension match
    ext = Path(p).suffix.lower()
    if ext and ext in ignore.extensions:
        return True

    # 4) Glob pattern match (relative paths)
    for pat in ignore.patterns:
        if fnmatch(p, pat):
            return True

    return False


def classify(age_days: int | None, *, is_ignored: bool) -> Status:
    """Classify into one of the four statuses."""
    if is_ignored:
        return "blue"
    # Edge case: missing commit timestamp. Fold into red for the four-color contract.
    if age_days is None:
        return "red"
    if age_days <= 7:
        return "green"
    if age_days <= 30:
        return "yellow"
    return "red"


def _sort_key_age_desc(item: dict[str, Any]) -> tuple[int, str]:
    # age_days descending, None last; stable tie-breaker by path.
    age = item.get("age_days")
    if isinstance(age, int):
        return (-age, cast(str, item.get("file", "")))
    return (10**9, cast(str, item.get("file", "")))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    _ = path.write_text(text, encoding="utf-8")


def generate_markdown(now: datetime, summary: dict[str, int], items: list[dict[str, Any]]) -> str:
    updated = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    lines: list[str] = []
    lines.append("# Repository File Status Report")
    lines.append("")
    lines.append(f"Last updated: **{updated}**")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- 🟢 Green: **{summary['green']}**")
    lines.append(f"- 🟡 Yellow: **{summary['yellow']}**")
    lines.append(f"- 🔴 Red: **{summary['red']}**")
    lines.append(f"- 🔵 Blue: **{summary['blue']}**")
    lines.append("")

    groups: dict[Status, list[dict[str, Any]]] = {"green": [], "yellow": [], "red": [], "blue": []}
    for it in items:
        groups[cast(Status, it["status"])].append(it)

    def render_section(title: str, status: Status, *, show_age: bool) -> None:
        lines.append(f"## {title}")
        lines.append("")
        if not groups[status]:
            lines.append("_None._")
            lines.append("")
            return
        for it in groups[status]:
            path = cast(str, it["file"])
            age = it.get("age_days")
            if show_age:
                if isinstance(age, int):
                    lines.append(f"- `{path}` — **{age}** days")
                else:
                    lines.append(f"- `{path}` — _unknown age_")
            else:
                lines.append(f"- `{path}`")
        lines.append("")

    render_section("🟢 Green (recent)", "green", show_age=True)
    render_section("🟡 Yellow (moderate)", "yellow", show_age=True)
    render_section("🔴 Red (stale)", "red", show_age=True)
    render_section("🔵 Blue (ignored)", "blue", show_age=False)

    return "\n".join(lines) + "\n"


def build_badge_fields(summary: dict[str, int]) -> dict[str, str]:
    """Return optional badge fields based on the worst present status."""
    red = summary["red"]
    yellow = summary["yellow"]
    green = summary["green"]
    blue = summary["blue"]
    total = red + yellow + green + blue

    if total == 0:
        return {"label": "freshness", "message": "no files", "color": "lightgrey"}
    if red > 0:
        return {"label": "freshness", "message": f"{red} stale", "color": "red"}
    if yellow > 0:
        return {"label": "freshness", "message": f"{yellow} moderate", "color": "yellow"}
    return {"label": "freshness", "message": f"{green} recent", "color": "brightgreen"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate repository file freshness reports.")
    _ = parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root (defaults to current directory; resolved via git when possible).",
    )
    _ = parser.add_argument(
        "--ignore-config",
        default="freshness_ignore.json",
        help=(
            "Path to ignore config JSON with keys: files, directories, extensions, patterns "
            "(all lists of strings)."
        ),
    )
    _ = parser.add_argument(
        "--output-markdown",
        default="docs/repo_file_status_report.md",
        help="Path to write Markdown dashboard.",
    )
    _ = parser.add_argument(
        "--output-details-json",
        default="file_freshness.json",
        help="Path to write per-file JSON details.",
    )
    _ = parser.add_argument(
        "--output-summary-json",
        default="freshness_summary.json",
        help="Path to write summary JSON counts (plus optional badge fields).",
    )
    args = cast(_Args, cast(object, parser.parse_args()))

    root = _resolve_repo_root(args.repo_root)
    ignore = load_ignore_config((root / args.ignore_config).resolve())
    now = _now_utc_from_env()

    files = _git_ls_files(root)
    items: list[dict[str, Any]] = []
    counts: dict[Status, int] = {"green": 0, "yellow": 0, "red": 0, "blue": 0}

    for rel_path in files:
        try:
            is_ignored = ignored_status(rel_path, ignore)
            commit_iso = _git_last_commit_iso(root, rel_path)
            age = _age_days(now, commit_iso)
            status = classify(age, is_ignored=is_ignored)
            counts[status] += 1
            items.append(
                {
                    "file": rel_path,
                    "last_commit": commit_iso,
                    "age_days": age,
                    "status": status,
                }
            )
        except Exception as exc:  # noqa: BLE001 - reliability: never fail per-file.
            print(f"[freshness] Warning: failed processing {rel_path}: {exc}", file=sys.stderr)
            status = "red"
            counts[status] += 1
            items.append({"file": rel_path, "last_commit": None, "age_days": None, "status": status})

    # Sorting rules: green/yellow/red by age desc; blue alpha.
    for s in ("green", "yellow", "red"):
        items_s = [it for it in items if it["status"] == s]
        items_s.sort(key=_sort_key_age_desc)
        # Replace in-place order by concatenation later.
    blue_items = [it for it in items if it["status"] == "blue"]
    blue_items.sort(key=lambda d: cast(str, d.get("file", "")).lower())
    ordered = (
        sorted((it for it in items if it["status"] == "green"), key=_sort_key_age_desc)
        + sorted((it for it in items if it["status"] == "yellow"), key=_sort_key_age_desc)
        + sorted((it for it in items if it["status"] == "red"), key=_sort_key_age_desc)
        + blue_items
    )

    summary: dict[str, int] = {
        "green": counts["green"],
        "yellow": counts["yellow"],
        "red": counts["red"],
        "blue": counts["blue"],
    }
    summary_out: dict[str, Any] = dict(summary)
    summary_out.update(build_badge_fields(summary))

    md_text = generate_markdown(now, summary, ordered)

    # Always generate outputs.
    write_json((root / args.output_details_json).resolve(), ordered)
    write_json((root / args.output_summary_json).resolve(), summary_out)
    out_md_path = (root / args.output_markdown).resolve()
    out_md_path.parent.mkdir(parents=True, exist_ok=True)
    _ = out_md_path.write_text(md_text, encoding="utf-8")

    return 0


if __name__ == "__main__":
    # Ensure a stable timezone in environments where TZ may be set oddly.
    os.environ.setdefault("TZ", "UTC")
    raise SystemExit(main())

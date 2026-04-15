#!/usr/bin/env python3
"""Generate repository file freshness reports using Git history.

This script:
- Lists only Git-tracked files (via ``git ls-files``).
- Computes each file's last update (via ``git log -1``) as ISO time and commit hash.
- Classifies files into green/yellow/red/blue using either commit-count or calendar-age
  thresholds, plus an ignore config (blue).
- Writes:
  - ``docs/repo_file_status_report.md`` (dashboard)
  - ``assets/file_freshness.json`` (per-file details)
  - ``assets/freshness_summary.json`` (counts + optional badge metadata)

Design notes:
- Git is the source of truth (no filesystem mtimes).
- A single file failing Git history lookup must not fail the whole run.
- ``--metric commits`` adds one ``git rev-list`` call per file; large monorepos may prefer
  ``--metric days``.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Literal, Protocol, cast

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Types and argparse protocol
# ---------------------------------------------------------------------------

Status = Literal["green", "yellow", "red", "blue"]
Metric = Literal["commits", "days"]


class _Args(Protocol):
    repo_root: str
    ignore_config: str
    output_markdown: str
    output_details_json: str
    output_summary_json: str
    metric: Metric
    green_max_commits: int
    yellow_max_commits: int


@dataclass(frozen=True)
class IgnoreConfig:
    """Ignore configuration loaded from the ignore JSON (e.g. ``assets/freshness_ignore.json``)."""

    files: frozenset[str]
    directories: tuple[str, ...]
    extensions: frozenset[str]
    patterns: tuple[str, ...]

    @classmethod
    def empty(cls) -> IgnoreConfig:
        """Return an ignore config that matches nothing (no paths ignored)."""
        return cls(files=frozenset(), directories=(), extensions=frozenset(), patterns=())


# ---------------------------------------------------------------------------
# Time (test hook via FRESHNESS_NOW_ISO)
# ---------------------------------------------------------------------------


def _now_utc() -> datetime:
    """Return current UTC time (used when ``FRESHNESS_NOW_ISO`` is unset)."""
    return datetime.now(UTC)


def _now_utc_from_env() -> datetime:
    """Return a deterministic 'now' when FRESHNESS_NOW_ISO is set (for tests)."""
    raw = os.environ.get("FRESHNESS_NOW_ISO")
    if not raw:
        return _now_utc()
    dt = _parse_git_iso_datetime(raw)
    if dt is None:
        logger.warning(
            f"invalid FRESHNESS_NOW_ISO (expected ISO-8601): {raw!r}"
        )
        return _now_utc()
    return dt


# ---------------------------------------------------------------------------
# Git subprocess adapters
# ---------------------------------------------------------------------------


def _run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str] | None:
    """Run ``git -C <root> <args>``; return None if the git executable is missing."""
    try:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:  # pragma: no cover -- git binary absent on PATH
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
    return [p.replace("\\", "/") for p in paths]


def _git_last_commit_hash_and_iso(root: Path, rel_path: str) -> tuple[str | None, str | None]:
    """Return (commit_hash, committer ISO time) for the last commit touching the path."""
    proc = _run_git(
        root,
        ["log", "-1", "--format=%H%x00%cI", "--", rel_path],
    )
    if proc is None or proc.returncode != 0:
        return None, None
    raw = proc.stdout.strip()
    if not raw or "\x00" not in raw:
        return None, None
    h, iso = raw.split("\x00", 1)
    h2, iso2 = h.strip(), iso.strip()
    if not h2 or not iso2:
        return None, None
    return h2, iso2


def _git_commits_since(root: Path, commit_sha: str) -> int | None:
    """Count commits reachable from HEAD but not from ``commit_sha`` (exclusive of that commit)."""
    spec = f"{commit_sha}..HEAD"
    proc = _run_git(root, ["rev-list", "--count", spec])
    if proc is None or proc.returncode != 0:
        return None
    text = proc.stdout.strip()
    if not text.isdigit():
        return None
    return int(text)


# ---------------------------------------------------------------------------
# Parsing and classification (pure helpers)
# ---------------------------------------------------------------------------


def _parse_git_iso_datetime(value: str) -> datetime | None:
    """Parse Git's ISO timestamp (e.g. 2026-04-08T12:34:56+00:00)."""
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _age_days(now: datetime, commit_iso: str | None) -> int | None:
    """Whole days from commit time to ``now``; None if commit time is unknown or invalid."""
    if commit_iso is None:
        return None
    dt = _parse_git_iso_datetime(commit_iso)
    if dt is None:
        return None
    delta = now - dt
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
        logger.warning(f"failed to read {path}: {exc}")
        return IgnoreConfig.empty()
    if not isinstance(raw, dict):
        logger.warning(f"ignore config root must be an object: {path}")
        return IgnoreConfig.empty()

    def get_list(key: str) -> list[str]:
        v = raw.get(key, [])
        if isinstance(v, list) and all(isinstance(x, str) for x in v):
            return cast("list[str]", v)
        logger.warning(
            f"ignore key {key!r} must be a list[str]: {path}"
        )
        return []

    files = frozenset(x.strip().replace("\\", "/") for x in get_list("files") if x.strip())
    directories = tuple(d for d in (_normalize_dir_prefix(x) for x in get_list("directories")) if d)
    extensions = frozenset(
        e for e in (_normalize_extension(x) for x in get_list("extensions")) if e
    )
    patterns = tuple(x.strip().replace("\\", "/") for x in get_list("patterns") if x.strip())

    return IgnoreConfig(
        files=files,
        directories=tuple(sorted(set(directories), key=str.lower)),
        extensions=extensions,
        patterns=tuple(sorted(set(patterns), key=str.lower)),
    )


def ignored_status(rel_path: str, ignore: IgnoreConfig) -> bool:
    """Return True if the path should be ignored (blue), per ignore priority."""
    p = rel_path.replace("\\", "/")

    if p in ignore.files:
        return True

    for d in ignore.directories:
        if p.startswith(d):
            return True

    ext = Path(p).suffix.lower()
    if ext and ext in ignore.extensions:
        return True

    return any(fnmatch(p, pat) for pat in ignore.patterns)


def classify_days(age_days: int | None, *, is_ignored: bool) -> Status:
    """Classify using calendar age: green <=2d, yellow (2,4], red >4 or unknown."""
    if is_ignored:
        return "blue"
    if age_days is None:
        return "red"
    if age_days <= 2:
        return "green"
    if age_days <= 4:
        return "yellow"
    return "red"


def classify_commits(
    commits_since: int | None,
    *,
    is_ignored: bool,
    green_max: int,
    yellow_max: int,
) -> Status:
    """Classify using commits after the last file change; unknown counts as red (non-blue)."""
    if is_ignored:
        return "blue"
    if commits_since is None:
        return "red"
    if commits_since <= green_max:
        return "green"
    if commits_since <= yellow_max:
        return "yellow"
    return "red"


def _sort_key_age_desc(item: dict[str, Any]) -> tuple[int, str]:
    """Generate a sort key for descending age (newest first).

    Items with missing age are sorted last.

    Args:
        item: File status dict with optional ``age_days`` and ``file`` keys.

    Returns:
        A tuple (negative_age, file_path) for descending-age sorting, or
        (large_number, file_path) for items with unknown age.
    """
    age = item.get("age_days")
    if isinstance(age, int):
        return (-age, cast("str", item.get("file", "")))
    return (10**9, cast("str", item.get("file", "")))


def _sort_key_commits_desc(item: dict[str, Any]) -> tuple[int, str]:
    """Generate a sort key for descending commit depth (most recent first).

    Items with missing commit counts are sorted last.

    Args:
        item: File status dict with optional ``commits_since`` and ``file`` keys.

    Returns:
        A tuple (negative_count, file_path) for descending-depth sorting, or
        (large_number, file_path) for items with unknown depth.
    """
    c = item.get("commits_since")
    if isinstance(c, int):
        return (-c, cast("str", item.get("file", "")))
    return (10**9, cast("str", item.get("file", "")))


# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------


def write_json(path: Path, data: Any) -> None:
    """Serialize data as JSON and write it to a file.

    Args:
        path: File path to write to (parent directory is created if missing).
        data: Object to serialize as JSON (will be sorted by keys).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    _ = path.write_text(text, encoding="utf-8")


def generate_markdown(
    now: datetime,
    summary: dict[str, int],
    items: list[dict[str, Any]],
    *,
    metric: Metric,
) -> str:
    """Render the freshness dashboard as Markdown.

    Args:
        now: Current time for the "last updated" timestamp.
        summary: Dict with counts of green/yellow/red/blue files.
        items: Ordered list of file status dicts.
        metric: Either ``commits`` or ``days`` (controls display format).

    Returns:
        Markdown text suitable for a status report document.
    """
    updated = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    lines: list[str] = []
    lines.append("# Repository File Status Report")
    lines.append("")
    lines.append(f"Last updated: **{updated}**")
    lines.append("")
    lines.append(f"_Metric: **{metric}**._")
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
        groups[cast("Status", it["status"])].append(it)

    def render_section(title: str, status: Status, *, show_metric: bool) -> None:
        lines.append(f"## {title}")
        lines.append("")
        if not groups[status]:
            lines.append("_None._")
            lines.append("")
            return
        for it in groups[status]:
            path = cast("str", it["file"])
            if not show_metric:
                lines.append(f"- `{path}`")
                continue
            if metric == "days":
                age = it.get("age_days")
                if isinstance(age, int):
                    lines.append(f"- `{path}` — **{age}** days")
                else:
                    lines.append(f"- `{path}` — _unknown age_")
            else:
                c = it.get("commits_since")
                if isinstance(c, int):
                    lines.append(f"- `{path}` — **{c}** commits since last change")
                else:
                    lines.append(f"- `{path}` — _unknown commit depth_")
        lines.append("")

    render_section("🟢 Green (recent)", "green", show_metric=True)
    render_section("🟡 Yellow (moderate)", "yellow", show_metric=True)
    render_section("🔴 Red (stale)", "red", show_metric=True)
    render_section("🔵 Blue (ignored)", "blue", show_metric=False)

    return "\n".join(lines).rstrip() + "\n"


def build_badge_fields(summary: dict[str, int]) -> dict[str, str]:
    """Compute optional badge metadata based on freshness status distribution.

    Args:
        summary: Dict with counts of green/yellow/red/blue files.

    Returns:
        A dict with keys ``label``, ``message``, ``color`` suitable for
        badge generation. Worst status wins (red > yellow > green > all-blue).
    """
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


# ---------------------------------------------------------------------------
# Core scan (orchestration)
# ---------------------------------------------------------------------------


def _classify_file_row(
    root: Path,
    rel_path: str,
    *,
    ignore: IgnoreConfig,
    now: datetime,
    metric: Metric,
    green_max_commits: int,
    yellow_max_commits: int,
) -> dict[str, Any]:
    """Compute freshness status and Git metadata for one file.

    Args:
        root: Repository root.
        rel_path: File path relative to root.
        ignore: Ignore configuration for classifying blue (ignored) files.
        now: Current time for age calculations.
        metric: Either ``commits`` or ``days`` for status classification.
        green_max_commits: Threshold for green status in commits metric.
        yellow_max_commits: Threshold for yellow status in commits metric.

    Returns:
        A dict with keys: ``file``, ``last_commit``, ``last_commit_sha``,
        ``age_days``, ``commits_since``, ``status``.
    """
    is_ignored = ignored_status(rel_path, ignore)
    commit_sha, commit_iso = _git_last_commit_hash_and_iso(root, rel_path)
    age = _age_days(now, commit_iso)
    commits_since: int | None = None
    if metric == "commits" and commit_sha is not None:
        commits_since = _git_commits_since(root, commit_sha)
    if metric == "commits":
        status = classify_commits(
            commits_since,
            is_ignored=is_ignored,
            green_max=green_max_commits,
            yellow_max=yellow_max_commits,
        )
    else:
        status = classify_days(age, is_ignored=is_ignored)

    return {
        "file": rel_path,
        "last_commit": commit_iso,
        "last_commit_sha": commit_sha,
        "age_days": age,
        "commits_since": commits_since,
        "status": status,
    }


def _safe_classify_file_row(
    root: Path,
    rel_path: str,
    *,
    ignore: IgnoreConfig,
    now: datetime,
    metric: Metric,
    green_max_commits: int,
    yellow_max_commits: int,
) -> dict[str, Any]:
    """Classify one file row, returning red status on any error instead of raising.

    Exceptions are logged but never re-raised, ensuring per-file failures do not
    stop the overall scan.

    Args:
        root: Repository root.
        rel_path: File path relative to root.
        ignore: Ignore configuration for classifying blue files.
        now: Current time for age calculations.
        metric: Either ``commits`` or ``days`` for status classification.
        green_max_commits: Threshold for green status in commits metric.
        yellow_max_commits: Threshold for yellow status in commits metric.

    Returns:
        A dict with the same shape as :func:`_classify_file_row`, or all-None
        fields with status=red if any error occurs.
    """
    try:
        return _classify_file_row(
            root,
            rel_path,
            ignore=ignore,
            now=now,
            metric=metric,
            green_max_commits=green_max_commits,
            yellow_max_commits=yellow_max_commits,
        )
    except Exception as exc:  # per-file reliability: log and continue
        logger.warning(f"failed processing {rel_path}: {exc}")
        return {
            "file": rel_path,
            "last_commit": None,
            "last_commit_sha": None,
            "age_days": None,
            "commits_since": None,
            "status": "red",
        }


def _aggregate_counts(items: list[dict[str, Any]]) -> dict[Status, int]:
    """Count files by status across all items.

    Args:
        items: List of file status dicts, each with a ``status`` key.

    Returns:
        A dict mapping status strings to occurrence counts.
    """
    counts: dict[Status, int] = {"green": 0, "yellow": 0, "red": 0, "blue": 0}
    for it in items:
        counts[cast("Status", it["status"])] += 1
    return counts


def _order_items_for_report(items: list[dict[str, Any]], *, metric: Metric) -> list[dict[str, Any]]:
    """Sort items by status and freshness metric for report output.

    Arranges items in order: green (fresh), yellow (moderate), red (stale),
    blue (ignored). Within each group, items are sorted by the metric
    (commits_since or age_days) in descending order.

    Args:
        items: File status dicts to sort.
        metric: Either ``commits`` (use commits_since) or ``days`` (use age_days).

    Returns:
        Sorted list of file status dicts.
    """
    sort_key = _sort_key_commits_desc if metric == "commits" else _sort_key_age_desc
    blue_items = [it for it in items if it["status"] == "blue"]
    blue_items.sort(key=lambda d: cast("str", d.get("file", "")).lower())
    return (
        sorted((it for it in items if it["status"] == "green"), key=sort_key)
        + sorted((it for it in items if it["status"] == "yellow"), key=sort_key)
        + sorted((it for it in items if it["status"] == "red"), key=sort_key)
        + blue_items
    )


def _validate_threshold_args(green_max: int, yellow_max: int) -> str | None:
    """Validate commit threshold arguments.

    Args:
        green_max: Maximum commits for green (fresh) status.
        yellow_max: Maximum commits for yellow (moderate) status.

    Returns:
        An error message for invalid thresholds, or ``None`` if valid.
    """
    if green_max < 0 or yellow_max < 0:
        return "[freshness] Error: commit thresholds must be non-negative."
    if green_max > yellow_max:
        return "[freshness] Error: --green-max-commits must be <= --yellow-max-commits."
    return None


def _parse_cli_args(argv: list[str] | None = None) -> _Args:
    """Parse command-line arguments for the freshness scanner.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Parsed arguments as an ``_Args`` protocol instance.
    """
    parser = argparse.ArgumentParser(description="Generate repository file freshness reports.")
    _ = parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root (defaults to current directory; resolved via git when possible).",
    )
    _ = parser.add_argument(
        "--ignore-config",
        default="assets/freshness_ignore.json",
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
        default="assets/file_freshness.json",
        help="Path to write per-file JSON details.",
    )
    _ = parser.add_argument(
        "--output-summary-json",
        default="assets/freshness_summary.json",
        help="Path to write summary JSON counts (plus optional badge fields).",
    )
    _ = parser.add_argument(
        "--metric",
        choices=("commits", "days"),
        default="commits",
        help="Classify by commits since last file change (default) or by calendar age in days.",
    )
    _ = parser.add_argument(
        "--green-max-commits",
        type=int,
        default=5,
        metavar="N",
        help="Commits mode: green if commits_since <= N (default: 5).",
    )
    _ = parser.add_argument(
        "--yellow-max-commits",
        type=int,
        default=20,
        metavar="N",
        help="Commits mode: yellow if commits_since <= N and > green max (default: 20).",
    )
    ns = parser.parse_args(argv)
    return cast("_Args", cast("object", ns))


def run_freshness_scan(args: _Args) -> tuple[list[dict[str, Any]], dict[str, Any], str]:
    """Scan the repository and classify all files by freshness.

    Args:
        args: Parsed CLI arguments with repo root, metric, thresholds, etc.

    Returns:
        A tuple of (ordered_items, summary_dict, markdown_text) ready for output.
    """
    root = _resolve_repo_root(args.repo_root)
    ignore = load_ignore_config((root / args.ignore_config).resolve())
    now = _now_utc_from_env()
    metric = cast("Metric", args.metric)

    files = _git_ls_files(root)
    items = [
        _safe_classify_file_row(
            root,
            rel,
            ignore=ignore,
            now=now,
            metric=metric,
            green_max_commits=args.green_max_commits,
            yellow_max_commits=args.yellow_max_commits,
        )
        for rel in files
    ]

    counts = _aggregate_counts(items)
    ordered = _order_items_for_report(items, metric=metric)

    summary: dict[str, int] = {
        "green": counts["green"],
        "yellow": counts["yellow"],
        "red": counts["red"],
        "blue": counts["blue"],
    }
    summary_out: dict[str, Any] = dict(summary)
    summary_out["metric"] = metric
    summary_out.update(build_badge_fields(summary))

    md_text = generate_markdown(now, summary, ordered, metric=metric)
    return ordered, summary_out, md_text


def write_freshness_artifacts(
    root: Path,
    args: _Args,
    ordered: list[dict[str, Any]],
    summary_out: dict[str, Any],
    md_text: str,
) -> None:
    """Write JSON and Markdown output files under ``root``.

    Creates parent directories as needed. Output paths are taken from ``args``.

    Args:
        root: Repository root directory.
        args: Parsed arguments containing output file paths.
        ordered: Ordered list of file status dicts for details JSON.
        summary_out: Summary dict for summary JSON (counts + metric + badges).
        md_text: Markdown text for the dashboard report.
    """
    write_json((root / args.output_details_json).resolve(), ordered)
    write_json((root / args.output_summary_json).resolve(), summary_out)
    out_md_path = (root / args.output_markdown).resolve()
    out_md_path.parent.mkdir(parents=True, exist_ok=True)
    _ = out_md_path.write_text(md_text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Run the freshness scanner CLI: validate args, scan, and write outputs.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        ``0`` on success, ``2`` if arguments are invalid.
    """
    args = _parse_cli_args(argv)
    err = _validate_threshold_args(args.green_max_commits, args.yellow_max_commits)
    if err is not None:
        logger.error(err)
        return 2

    root = _resolve_repo_root(args.repo_root)
    ordered, summary_out, md_text = run_freshness_scan(args)
    write_freshness_artifacts(root, args, ordered, summary_out, md_text)
    return 0


if __name__ == "__main__":
    os.environ.setdefault("TZ", "UTC")
    raise SystemExit(main())

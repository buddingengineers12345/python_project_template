"""Tests for ``scripts/repo_file_freshness`` classification and outputs."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def run_command(
    cmd: list[str],
    cwd: Path,
    *,
    check: bool = True,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess under ``cwd`` with optional extra environment variables."""
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True, env=env)


def git_init(repo: Path) -> None:
    """Initialize a git repo with a fixed user identity for deterministic commits."""
    run_command(["git", "init"], cwd=repo)
    run_command(["git", "config", "user.name", "Test User"], cwd=repo)
    run_command(["git", "config", "user.email", "test@example.com"], cwd=repo)


def git_commit(repo: Path, message: str, *, commit_date_iso: str) -> None:
    """Create a commit touching tracked files with fixed author/committer dates."""
    env = {"GIT_AUTHOR_DATE": commit_date_iso, "GIT_COMMITTER_DATE": commit_date_iso}
    run_command(["git", "add", "-A"], cwd=repo, extra_env=env)
    run_command(["git", "commit", "-m", message], cwd=repo, extra_env=env)


def git_empty_commit(repo: Path, message: str, *, commit_date_iso: str) -> None:
    """Create an empty commit with fixed author/committer dates."""
    env = {"GIT_AUTHOR_DATE": commit_date_iso, "GIT_COMMITTER_DATE": commit_date_iso}
    run_command(["git", "commit", "--allow-empty", "-m", message], cwd=repo, extra_env=env)


def write_ignore(repo: Path, data: object) -> None:
    """Write ``assets/freshness_ignore.json`` for the freshness script."""
    assets = repo / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "freshness_ignore.json").write_text(json.dumps(data) + "\n", encoding="utf-8")


def run_script(repo: Path, *extra_args: str) -> None:
    """Run ``repo_file_freshness.py`` against ``repo`` with a fixed reference time."""
    script = Path(__file__).resolve().parent.parent / "scripts" / "repo_file_freshness.py"
    run_command(
        [
            sys.executable,
            str(script),
            "--repo-root",
            str(repo),
            *extra_args,
        ],
        cwd=repo,
        extra_env={"FRESHNESS_NOW_ISO": "2026-04-08T00:00:00+00:00"},
    )


def load_details(repo: Path) -> list[dict[str, object]]:
    """Load ``assets/file_freshness.json`` as a list of per-file detail dicts."""
    raw = json.loads((repo / "assets" / "file_freshness.json").read_text(encoding="utf-8"))
    assert isinstance(raw, list)
    return raw


def by_file(items: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    """Index freshness detail rows by file path."""
    out: dict[str, dict[str, object]] = {}
    for it in items:
        out[str(it["file"])] = it
    return out


def test_classification_green_yellow_red_days(tmp_path: Path) -> None:
    """Days mode: green <=2d, yellow (2,4], red >4 (reference 2026-04-08)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git_init(repo)
    (repo / "assets").mkdir(parents=True, exist_ok=True)
    (repo / "assets" / "freshness_ignore.json").write_text(
        json.dumps({"files": [], "directories": [], "extensions": [], "patterns": []}) + "\n",
        encoding="utf-8",
    )

    (repo / "recent.txt").write_text("recent\n", encoding="utf-8")
    git_commit(repo, "add recent", commit_date_iso="2026-04-07T00:00:00+00:00")

    (repo / "mid.txt").write_text("mid\n", encoding="utf-8")
    git_commit(repo, "add mid", commit_date_iso="2026-04-05T00:00:00+00:00")

    (repo / "old.txt").write_text("old\n", encoding="utf-8")
    git_commit(repo, "add old", commit_date_iso="2026-04-02T00:00:00+00:00")

    run_script(repo, "--metric", "days")
    items = by_file(load_details(repo))
    assert items["recent.txt"]["status"] == "green"
    assert items["mid.txt"]["status"] == "yellow"
    assert items["old.txt"]["status"] == "red"


def test_classification_commits_since_last_change(tmp_path: Path) -> None:
    """Commits metric counts commits since the last change to each file."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git_init(repo)
    (repo / "assets").mkdir(parents=True, exist_ok=True)
    (repo / "assets" / "freshness_ignore.json").write_text(
        json.dumps({"files": [], "directories": [], "extensions": [], "patterns": []}) + "\n",
        encoding="utf-8",
    )

    (repo / "tracked.txt").write_text("v1\n", encoding="utf-8")
    git_commit(repo, "touch file", commit_date_iso="2026-01-01T00:00:00+00:00")
    git_empty_commit(repo, "empty 1", commit_date_iso="2026-01-02T00:00:00+00:00")
    git_empty_commit(repo, "empty 2", commit_date_iso="2026-01-03T00:00:00+00:00")

    run_script(
        repo,
        "--metric",
        "commits",
        "--green-max-commits",
        "1",
        "--yellow-max-commits",
        "5",
    )
    items = by_file(load_details(repo))
    assert items["tracked.txt"]["commits_since"] == 2
    assert items["tracked.txt"]["status"] == "yellow"


def test_ignore_priority_exact_then_dir_then_ext_then_pattern(tmp_path: Path) -> None:
    """Ignore rules apply in file, directory, extension, then glob order."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git_init(repo)

    (repo / "src").mkdir()
    (repo / "src" / "main.py").write_text("print('x')\n", encoding="utf-8")
    (repo / "build").mkdir()
    (repo / "build" / "out.js").write_text("console.log('x')\n", encoding="utf-8")
    (repo / "docs.md").write_text("# doc\n", encoding="utf-8")
    (repo / "exact.txt").write_text("x\n", encoding="utf-8")

    git_commit(repo, "add files", commit_date_iso="2025-01-01T00:00:00+00:00")

    write_ignore(
        repo,
        {
            "files": ["exact.txt"],
            "directories": ["build/"],
            "extensions": [".md"],
            "patterns": ["src/*.py"],
        },
    )

    run_script(repo, "--metric", "days")
    items = by_file(load_details(repo))
    assert items["exact.txt"]["status"] == "blue"
    assert items["build/out.js"]["status"] == "blue"
    assert items["docs.md"]["status"] == "blue"
    assert items["src/main.py"]["status"] == "blue"


def test_invalid_ignore_config_is_graceful(tmp_path: Path) -> None:
    """Malformed ignore JSON does not crash the script; files still get a status."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git_init(repo)
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    git_commit(repo, "add a", commit_date_iso="2025-01-01T00:00:00+00:00")

    assets = repo / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "freshness_ignore.json").write_text("{not-json}\n", encoding="utf-8")
    run_script(repo, "--metric", "days")

    items = by_file(load_details(repo))
    assert items["a.txt"]["status"] in {"green", "yellow", "red", "blue"}


def test_empty_repo_generates_outputs(tmp_path: Path) -> None:
    """An empty repo still produces JSON and Markdown outputs."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git_init(repo)

    run_script(repo)
    assert (repo / "assets" / "file_freshness.json").is_file()
    assert (repo / "assets" / "freshness_summary.json").is_file()
    assert (repo / "docs" / "repo_file_status_report.md").is_file()

"""Tests for ``scripts/check_root_template_sync`` policy checks."""

from __future__ import annotations

import contextlib
import io
import json
import sys
from dataclasses import dataclass
from pathlib import Path  # noqa: TC003

import pytest
from tests.script_imports import REPO_ROOT, load_script_module

_SCRIPT = REPO_ROOT / "scripts" / "check_root_template_sync.py"
crs = load_script_module("check_root_template_sync")


@dataclass
class _Result:
    returncode: int
    stdout: str
    stderr: str = ""


def write_file(path: Path, content: str) -> None:
    """Create parent directories and write ``content`` to ``path`` as UTF-8 text."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_sync_check(repo_root: Path, map_rel: str = "docs/map.yaml") -> _Result:
    """Run the sync checker in-process and return a result with returncode + stdout."""
    buf = io.StringIO()
    saved_argv = sys.argv
    try:
        sys.argv = [str(_SCRIPT), "--repo-root", str(repo_root), "--map", map_rel]
        with contextlib.redirect_stdout(buf):
            try:
                returncode = crs.main()
            except SystemExit as exc:
                returncode = int(exc.code) if exc.code is not None else 0
    finally:
        sys.argv = saved_argv
    return _Result(returncode=returncode, stdout=buf.getvalue())


def test_sync_check_passes_for_matching_pairs_and_sections(tmp_path: Path) -> None:
    """Matching workflow, hook, and pyproject sections yield exit code 0."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "workflow_versions",
                "type": "workflow_action_versions",
                "pairs": [
                    {
                        "root": ".github/workflows/lint.yml",
                        "template": "template/.github/workflows/lint.yml.jinja",
                    }
                ],
            },
            {
                "id": "hooks",
                "type": "exact_file_pairs",
                "pairs": [
                    {
                        "root": ".claude/hooks/pre-bash-block-no-verify.sh",
                        "template": "template/.claude/hooks/pre-bash-block-no-verify.sh",
                    }
                ],
            },
            {
                "id": "pyproject",
                "type": "pyproject_sections",
                "root": "pyproject.toml",
                "template": "template/pyproject.toml.jinja",
                "sections": [
                    {"name": "tool.ruff", "required_keys": ["line-length", "target-version"]},
                    {
                        "name": "tool.ruff.lint",
                        "required_keys": ["select", "ignore"],
                        "required_select_codes": ["D", "T20"],
                    },
                ],
            },
        ],
    }
    write_file(repo / "docs" / "map.yaml", json.dumps(map_data, indent=2))

    write_file(
        repo / ".github/workflows/lint.yml",
        "jobs:\n  lint:\n    steps:\n      - uses: actions/checkout@v6\n",
    )
    write_file(
        repo / "template/.github/workflows/lint.yml.jinja",
        "jobs:\n  lint:\n    steps:\n      - uses: actions/checkout@v6\n",
    )

    hook_content = "#!/usr/bin/env bash\necho ok\n"
    write_file(repo / ".claude/hooks/pre-bash-block-no-verify.sh", hook_content)
    write_file(repo / "template/.claude/hooks/pre-bash-block-no-verify.sh", hook_content)

    write_file(
        repo / "pyproject.toml",
        (
            "[tool.ruff]\n"
            "line-length = 100\n"
            'target-version = "py311"\n\n'
            "[tool.ruff.lint]\n"
            'select = ["D", "T20"]\n'
            'ignore = ["E501"]\n'
        ),
    )
    write_file(
        repo / "template/pyproject.toml.jinja",
        (
            "{% if true %}\n{% endif %}\n"
            "[tool.ruff]\n"
            "line-length = 100\n"
            "target-version = \"py{{ python_min_version | replace('.', '') }}\"\n\n"
            "[tool.ruff.lint]\n"
            'select = ["D", "T20", "UP"]\n'
            'ignore = ["E501"]\n'
        ),
    )

    result = run_sync_check(repo)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[sync-check] PASS" in result.stdout


def test_sync_check_fails_on_workflow_action_version_drift(tmp_path: Path) -> None:
    """Mismatched ``uses:`` versions between root and template fail the check."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "workflow_versions",
                "type": "workflow_action_versions",
                "pairs": [
                    {
                        "root": ".github/workflows/security.yml",
                        "template": "template/.github/workflows/security.yml.jinja",
                    }
                ],
            }
        ],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    write_file(
        repo / ".github/workflows/security.yml",
        "jobs:\n  s:\n    steps:\n      - uses: github/codeql-action/init@v4\n",
    )
    write_file(
        repo / "template/.github/workflows/security.yml.jinja",
        "jobs:\n  s:\n    steps:\n      - uses: github/codeql-action/init@v3\n",
    )

    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "workflow_versions" in result.stdout
    assert "mismatch" in result.stdout


def test_sync_check_fails_when_required_pyproject_key_missing(tmp_path: Path) -> None:
    """Missing required TOML keys in the template fail the pyproject section check."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "pyproject",
                "type": "pyproject_sections",
                "root": "pyproject.toml",
                "template": "template/pyproject.toml.jinja",
                "sections": [{"name": "tool.basedpyright", "required_keys": ["typeCheckingMode"]}],
            }
        ],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    write_file(repo / "pyproject.toml", '[tool.basedpyright]\ntypeCheckingMode = "standard"\n')
    write_file(
        repo / "template/pyproject.toml.jinja", '[tool.basedpyright]\npythonVersion = "3.11"\n'
    )

    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "missing key in template" in result.stdout


def test_load_map_rejects_invalid_json(tmp_path: Path) -> None:
    """``_load_map`` raises when the file is not valid JSON."""
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        crs._load_map(bad)


def test_load_map_rejects_non_object_root(tmp_path: Path) -> None:
    """Top-level JSON must be an object."""
    p = tmp_path / "list.json"
    p.write_text("[1]", encoding="utf-8")
    with pytest.raises(ValueError, match="object"):
        crs._load_map(p)


def test_main_empty_checks_returns_exit_code_2(tmp_path: Path) -> None:
    """An empty ``checks`` array is a fatal mapping error (exit 2)."""
    repo = tmp_path / "repo"
    write_file(repo / "docs/map.yaml", json.dumps({"version": 1, "checks": []}, indent=2))
    result = run_sync_check(repo)
    assert result.returncode == 2
    assert "non-empty checks" in result.stdout


def test_main_malformed_map_json_returns_exit_code_2(tmp_path: Path) -> None:
    """Invalid JSON in the map file yields exit code 2."""
    repo = tmp_path / "repo"
    write_file(repo / "docs/map.yaml", "{")
    result = run_sync_check(repo)
    assert result.returncode == 2
    assert "invalid JSON" in result.stdout


def test_unsupported_check_type_is_a_violation(tmp_path: Path) -> None:
    """Unknown ``type`` values surface as a check violation (exit 1)."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [{"id": "weird", "type": "not_a_real_check_type"}],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "weird" in result.stdout
    assert "unsupported check type" in result.stdout


def test_invalid_pairs_raises_as_check_violation(tmp_path: Path) -> None:
    """Workflow check with no valid root/template pairs fails via that check's id."""
    repo = tmp_path / "repo"
    map_data = {
        "version": 1,
        "checks": [
            {
                "id": "wf_bad_pairs",
                "type": "workflow_action_versions",
                "pairs": [{"root": 1, "template": 2}],
            }
        ],
    }
    write_file(repo / "docs/map.yaml", json.dumps(map_data, indent=2))
    result = run_sync_check(repo)
    assert result.returncode == 1
    assert "wf_bad_pairs" in result.stdout
    assert "pairs must contain" in result.stdout

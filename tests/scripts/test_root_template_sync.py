"""Tests for ``scripts/check_root_template_sync`` policy checks."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tests._paths import REPO_ROOT


def write_file(path: Path, content: str) -> None:
    """Create parent directories and write ``content`` to ``path`` as UTF-8 text."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_sync_check(
    repo_root: Path, map_rel: str = "docs/map.yaml"
) -> subprocess.CompletedProcess[str]:
    """Run the root/template sync checker subprocess and return its result."""
    script = REPO_ROOT / "scripts" / "check_root_template_sync.py"
    return subprocess.run(
        [
            sys.executable,
            str(script),
            "--repo-root",
            str(repo_root),
            "--map",
            map_rel,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


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

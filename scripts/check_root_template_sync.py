#!/usr/bin/env python3
"""Validate root/template sync policy mappings."""

from __future__ import annotations

import argparse
import difflib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SECTION_HEADER_RE = re.compile(r"^\[([^\]]+)\]\s*$", flags=re.MULTILINE)
USES_RE = re.compile(r"uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*)@([^\s]+)")
ASSIGNMENT_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*=", flags=re.MULTILINE)
QUOTED_TOKEN_RE = re.compile(r'"([^"]+)"')


@dataclass(frozen=True)
class Violation:
    """Single sync violation emitted by one check."""

    check_id: str
    message: str


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _load_map(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(_read_text(path))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON/YAML mapping file {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("mapping root must be an object")
    return raw


def _validate_pairs_object(check_id: str, obj: Any) -> list[dict[str, str]]:
    if not isinstance(obj, list):
        return []
    valid: list[dict[str, str]] = []
    for item in obj:
        if not isinstance(item, dict):
            continue
        root_path = item.get("root")
        tpl_path = item.get("template")
        if isinstance(root_path, str) and isinstance(tpl_path, str):
            valid.append({"root": root_path, "template": tpl_path})
    if not valid:
        raise ValueError(f"{check_id}: pairs must contain at least one root/template mapping")
    return valid


def _extract_workflow_actions(text: str) -> dict[str, set[str]]:
    actions: dict[str, set[str]] = {}
    for action, version in USES_RE.findall(text):
        versions = actions.setdefault(action, set())
        versions.add(version.strip())
    return actions


def _check_workflow_action_versions(check: dict[str, Any], repo_root: Path) -> list[Violation]:
    check_id = str(check.get("id", "workflow_action_versions"))
    pairs = _validate_pairs_object(check_id, check.get("pairs"))
    violations: list[Violation] = []
    for pair in pairs:
        violations.extend(_workflow_pair_violations(check_id, pair, repo_root))
    return violations


def _workflow_pair_violations(check_id: str, pair: dict[str, str], repo_root: Path) -> list[Violation]:
    root_path = repo_root / pair["root"]
    tpl_path = repo_root / pair["template"]
    if not root_path.is_file():
        return [Violation(check_id, f"missing file: {pair['root']}")]
    if not tpl_path.is_file():
        return [Violation(check_id, f"missing file: {pair['template']}")]

    root_actions = _extract_workflow_actions(_read_text(root_path))
    tpl_actions = _extract_workflow_actions(_read_text(tpl_path))
    shared = sorted(set(root_actions).intersection(tpl_actions))
    if not shared:
        return [
            Violation(
                check_id,
                f"{pair['root']} <-> {pair['template']}: no shared actions to compare",
            )
        ]

    violations: list[Violation] = []
    for action in shared:
        if root_actions[action] == tpl_actions[action]:
            continue
        violations.append(
            Violation(
                check_id,
                (
                    f"{pair['root']} <-> {pair['template']}: action {action} mismatch "
                    f"(root={sorted(root_actions[action])}, template={sorted(tpl_actions[action])})"
                ),
            )
        )
    return violations


def _normalize_for_exact_compare(text: str) -> str:
    return text.replace("\r\n", "\n")


def _short_diff(left: str, right: str, *, max_lines: int = 12) -> str:
    lines = list(
        difflib.unified_diff(
            left.splitlines(),
            right.splitlines(),
            fromfile="root",
            tofile="template",
            lineterm="",
        )
    )
    if not lines:
        return "content differs"
    return " | ".join(lines[:max_lines])


def _check_exact_file_pairs(check: dict[str, Any], repo_root: Path) -> list[Violation]:
    check_id = str(check.get("id", "exact_file_pairs"))
    pairs = _validate_pairs_object(check_id, check.get("pairs"))
    violations: list[Violation] = []

    for pair in pairs:
        root_path = repo_root / pair["root"]
        tpl_path = repo_root / pair["template"]
        if not root_path.is_file():
            violations.append(Violation(check_id, f"missing file: {pair['root']}"))
            continue
        if not tpl_path.is_file():
            violations.append(Violation(check_id, f"missing file: {pair['template']}"))
            continue

        root_text = _normalize_for_exact_compare(_read_text(root_path))
        tpl_text = _normalize_for_exact_compare(_read_text(tpl_path))
        if root_text != tpl_text:
            diff = _short_diff(root_text, tpl_text)
            violations.append(
                Violation(
                    check_id,
                    f"{pair['root']} <-> {pair['template']}: exact mismatch ({diff})",
                )
            )
    return violations


def _strip_jinja_lines(text: str) -> str:
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("{%") and stripped.endswith("%}"):
            continue
        if stripped.startswith("{#") and stripped.endswith("#}"):
            continue
        kept.append(line)
    return "\n".join(kept) + "\n"


def _extract_section_text(text: str, section_name: str) -> str | None:
    matches = list(SECTION_HEADER_RE.finditer(text))
    for idx, match in enumerate(matches):
        if match.group(1).strip() != section_name:
            continue
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        return text[start:end]
    return None


def _extract_assignment_keys(section_text: str) -> set[str]:
    return {m.group(1).strip() for m in ASSIGNMENT_RE.finditer(section_text)}


def _extract_select_codes(section_text: str) -> set[str]:
    select_match = re.search(r"^\s*select\s*=\s*\[(.*?)\]", section_text, flags=re.MULTILINE | re.DOTALL)
    if not select_match:
        return set()
    body = select_match.group(1)
    return {token.strip() for token in QUOTED_TOKEN_RE.findall(body)}


def _check_pyproject_sections(check: dict[str, Any], repo_root: Path) -> list[Violation]:
    check_id = str(check.get("id", "pyproject_sections"))
    root_rel = check.get("root")
    template_rel = check.get("template")
    sections = check.get("sections")
    if not isinstance(root_rel, str) or not isinstance(template_rel, str) or not isinstance(sections, list):
        raise ValueError(f"{check_id}: root/template/sections are required")

    root_path = repo_root / root_rel
    template_path = repo_root / template_rel
    if not root_path.is_file():
        return [Violation(check_id, f"missing file: {root_rel}")]
    if not template_path.is_file():
        return [Violation(check_id, f"missing file: {template_rel}")]

    root_text = _read_text(root_path)
    template_text = _strip_jinja_lines(_read_text(template_path))
    return _collect_pyproject_section_violations(check_id, sections, root_text, template_text)


def _collect_pyproject_section_violations(
    check_id: str,
    sections: list[Any],
    root_text: str,
    template_text: str,
) -> list[Violation]:
    violations: list[Violation] = []
    for section_def in sections:
        violations.extend(_pyproject_section_violations(check_id, section_def, root_text, template_text))
    return violations


def _pyproject_section_violations(
    check_id: str,
    section_def: Any,
    root_text: str,
    template_text: str,
) -> list[Violation]:
    if not isinstance(section_def, dict):
        return [Violation(check_id, "section definition must be an object")]

    section_name = section_def.get("name")
    if not isinstance(section_name, str):
        return [Violation(check_id, "section is missing name")]

    root_section = _extract_section_text(root_text, section_name)
    template_section = _extract_section_text(template_text, section_name)
    if root_section is None:
        return [Violation(check_id, f"missing root section: [{section_name}]")]
    if template_section is None:
        return [Violation(check_id, f"missing template section: [{section_name}]")]

    violations: list[Violation] = []
    violations.extend(_required_key_violations(check_id, section_name, root_section, template_section, section_def))
    violations.extend(_required_select_code_violations(check_id, section_name, root_section, template_section, section_def))
    return violations


def _required_key_violations(
    check_id: str,
    section_name: str,
    root_section: str,
    template_section: str,
    section_def: dict[str, Any],
) -> list[Violation]:
    required_keys = section_def.get("required_keys", [])
    if not isinstance(required_keys, list):
        return []

    root_keys = _extract_assignment_keys(root_section)
    template_keys = _extract_assignment_keys(template_section)
    violations: list[Violation] = []
    for key in required_keys:
        if not isinstance(key, str):
            continue
        if key not in root_keys:
            violations.append(Violation(check_id, f"[{section_name}] missing key in root baseline: {key}"))
        if key not in template_keys:
            violations.append(Violation(check_id, f"[{section_name}] missing key in template: {key}"))
    return violations


def _required_select_code_violations(
    check_id: str,
    section_name: str,
    root_section: str,
    template_section: str,
    section_def: dict[str, Any],
) -> list[Violation]:
    required_codes = section_def.get("required_select_codes", [])
    if not isinstance(required_codes, list):
        return []

    root_codes = _extract_select_codes(root_section)
    template_codes = _extract_select_codes(template_section)
    violations: list[Violation] = []
    for code in required_codes:
        if not isinstance(code, str):
            continue
        if code not in root_codes:
            violations.append(Violation(check_id, f"[{section_name}] root select list missing code: {code}"))
        if code not in template_codes:
            violations.append(Violation(check_id, f"[{section_name}] template select list missing code: {code}"))
    return violations


def _run_check(check: dict[str, Any], repo_root: Path) -> list[Violation]:
    check_type = check.get("type")
    if check_type == "workflow_action_versions":
        return _check_workflow_action_versions(check, repo_root)
    if check_type == "exact_file_pairs":
        return _check_exact_file_pairs(check, repo_root)
    if check_type == "pyproject_sections":
        return _check_pyproject_sections(check, repo_root)
    check_id = str(check.get("id", "unknown"))
    return [Violation(check_id, f"unsupported check type: {check_type!r}")]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check root/template sync policy mappings.")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root containing mapped files (defaults to script parent).",
    )
    parser.add_argument(
        "--map",
        default="docs/root-template-sync-map.yaml",
        help="Mapping file path (JSON content in YAML file supported).",
    )
    args = parser.parse_args()

    repo_root = (
        Path(args.repo_root).resolve()
        if isinstance(args.repo_root, str) and args.repo_root
        else Path(__file__).resolve().parent.parent
    )
    map_path = (repo_root / args.map).resolve()
    if not map_path.is_file():
        print(f"[sync-check] ERROR: mapping file not found: {map_path}")
        return 2

    try:
        mapping = _load_map(map_path)
    except ValueError as exc:
        print(f"[sync-check] ERROR: {exc}")
        return 2

    checks = mapping.get("checks", [])
    if not isinstance(checks, list) or not checks:
        print("[sync-check] ERROR: mapping must define a non-empty checks list")
        return 2

    violations: list[Violation] = []
    for raw_check in checks:
        if not isinstance(raw_check, dict):
            violations.append(Violation("mapping", "each check entry must be an object"))
            continue
        try:
            violations.extend(_run_check(raw_check, repo_root))
        except ValueError as exc:
            check_id = str(raw_check.get("id", "invalid-check"))
            violations.append(Violation(check_id, str(exc)))

    if violations:
        print(f"[sync-check] FAIL: found {len(violations)} sync violation(s)")
        for item in violations:
            print(f" - [{item.check_id}] {item.message}")
        return 1

    print("[sync-check] PASS: root/template sync map checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

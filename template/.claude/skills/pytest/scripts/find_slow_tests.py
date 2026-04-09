#!/usr/bin/env python3
"""Find slow-running test functions by analysing pytest duration output.

Runs pytest with --durations=0 (all tests) and reports any test whose duration
exceeds a configurable threshold. Output is a JSON array so other tools can
consume it, plus a human-readable summary on stderr.

Usage:
    python find_slow_tests.py                        # default 1.0s threshold
    python find_slow_tests.py --threshold 0.5        # 500ms threshold
    python find_slow_tests.py --threshold 2.0 --top 5  # top 5 above 2s
    python find_slow_tests.py --json-only            # suppress human summary
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SlowTest:
    """A test that exceeded the duration threshold."""

    nodeid: str
    duration: float
    file_path: str
    function_name: str
    line_hint: str


# pytest --durations output looks like:
# 1.23s call     tests/test_core.py::test_heavy_computation
_DURATION_RE = re.compile(
    r"^\s*(?P<duration>[\d.]+)s\s+(?P<phase>call|setup|teardown)\s+(?P<nodeid>.+)$"
)


def run_pytest_durations(test_path: str | None = None) -> str:
    """Run pytest --durations=0 and return the raw stdout."""
    cmd = [sys.executable, "-m", "pytest", "--durations=0", "-q", "--tb=no", "--no-header"]
    if test_path:
        cmd.append(test_path)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    return result.stdout


def parse_durations(output: str, threshold: float) -> list[SlowTest]:
    """Parse pytest duration lines and return tests above the threshold."""
    slow: list[SlowTest] = []

    for line in output.splitlines():
        match = _DURATION_RE.match(line)
        if not match:
            continue

        # Only care about the 'call' phase — setup/teardown are fixture overhead
        if match.group("phase") != "call":
            continue

        duration = float(match.group("duration"))
        if duration < threshold:
            continue

        nodeid = match.group("nodeid").strip()
        # nodeid format: tests/test_core.py::TestClass::test_method
        # or:            tests/test_core.py::test_function
        parts = nodeid.split("::")
        file_path = parts[0] if parts else nodeid
        function_name = parts[-1] if len(parts) > 1 else ""

        # Build a grep-friendly hint: "file_path:def function_name"
        line_hint = f"{file_path}:def {function_name}"

        slow.append(
            SlowTest(
                nodeid=nodeid,
                duration=duration,
                file_path=file_path,
                function_name=function_name,
                line_hint=line_hint,
            )
        )

    # Sort slowest first
    slow.sort(key=lambda t: t.duration, reverse=True)
    return slow


def main() -> None:
    """Entry point for find_slow_tests."""
    parser = argparse.ArgumentParser(
        description="Find pytest tests that exceed a duration threshold."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=1.0,
        help="Duration threshold in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=0,
        help="Only show top N slowest tests (0 = all, default: 0)",
    )
    parser.add_argument(
        "--test-path",
        type=str,
        default=None,
        help="Path to a specific test file or directory (default: all tests)",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Output JSON only, suppress human-readable summary",
    )
    args = parser.parse_args()

    output = run_pytest_durations(args.test_path)
    slow_tests = parse_durations(output, args.threshold)

    if args.top > 0:
        slow_tests = slow_tests[: args.top]

    # JSON on stdout (avoid print — ruff T201 in repo template)
    sys.stdout.write(json.dumps([asdict(t) for t in slow_tests], indent=2) + "\n")

    # Human summary on stderr
    if not args.json_only:
        if not slow_tests:
            sys.stderr.write(f"\n  No tests exceeded {args.threshold}s threshold.\n")
        else:
            sys.stderr.write(
                f"\n  Found {len(slow_tests)} test(s) exceeding {args.threshold}s:\n\n"
            )
            for t in slow_tests:
                marker = "  SLOW " if t.duration >= args.threshold * 2 else "  slow "
                sys.stderr.write(f"{marker} {t.duration:6.2f}s  {t.nodeid}\n")
            sys.stderr.write("\n")


if __name__ == "__main__":
    main()

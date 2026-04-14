---
name: sdlc-workflow
description: >-
  Master SDLC orchestrator that reads TASK.md and executes a complete development
  cycle: TDD test design, TDD implementation, refactoring, code quality, security,
  documentation, git commit, and pull request. Use this skill whenever TASK.md is
  updated or the user says "run the pipeline", "implement this task", "start the
  workflow", "SDLC", "implement from TASK.md", or any request to execute the full
  development lifecycle from a task description.
---

# SDLC Workflow Skill

This skill orchestrates the full software development lifecycle from a task description
in `TASK.md` through to a pull request. It delegates to sub-skills and uses Agent tool
calls with model overrides for mechanical stages.

**Hard rules — never break these:**
- No implementation code before a failing test exists.
- No refactoring before GREEN is confirmed.
- No commit before `just ci` exits 0.
- No patching bugs without first writing a reproducing test.
- Every test must have a pytest marker.

---

## Stage banner

Display this banner at the top of every response. Use `✓` for completed, `●` for
current, `○` for upcoming.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SDLC  ○DESIGN  ○RED  ○GREEN  ○REFACTOR  ○QUALITY  ○SECURE  ○DOCS  ○COMMIT  ○PR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Stage pipeline

```
Stage   Name                    Model    Execution          Sub-skills
-----   --------------------    ------   ----------------   -------------------------
  0     DISCOVER                Full     Main model         (reads YAML)
  0.5   PRE-FLIGHT              Haiku    Agent call         (automated checks)
  1     RED                     Full     Main model         pytest
  2     GREEN                   Full     Main model         pytest
  2.5   CONTRACT (conditional)  Haiku    Agent call         (API guard)
  3     REFACTOR                Sonnet   Agent call         python-docstrings
  3.5   PERF (conditional)      Haiku    Agent call         (benchmarks)
  4     CODE QUALITY            Haiku    Agent (parallel)   linting, type-checking
  5     SECURITY                Haiku    Agent (parallel)   security
  6     DOCUMENTATION           Haiku    Agent (parallel)   python-docstrings, markdown
  7     COMMIT + CHANGELOG      Haiku    Agent (sequential) (inline guidance)
  8     PULL REQUEST            Haiku    Agent (sequential) prepare_pr
```

Conditional stages (2.5, 3.5) only activate when flagged in task YAML.

---

## Stage 0 — DISCOVER: Read task YAML

1. Read `tasks/TASK_ID.yaml`. Parse: task_id, type, status, requirement,
   acceptance_criteria, constraints, files_affected, testing_strategy, and changelog entry.
2. Read `assets/task_template.yaml` for YAML schema reference.
3. Run `just preflight TASK_ID` to execute pre-flight checks.
4. This project uses `just test` for tests and `just ci` for full CI.
5. Explore the codebase: `pyproject.toml`, `conftest.py`, existing tests, target modules.
6. Create `task_channel/task_TASK_ID/` directory for persistent artifacts.
7. Output: requirement summary, acceptance criteria list, files that will change.
8. Get user approval before proceeding.

---

## Stage 0.5 — PRE-FLIGHT: Automated checks

1. Run `just preflight TASK_ID`.
2. If any check fails, stop the pipeline and report the failure.
3. If all checks pass, proceed to Stage 1.

Gate: all pre-flight checks pass. No user approval needed.

---

## Stage 1 — RED: Write failing tests

**Model:** Full (main model, interactive)

1. Load the `pytest` skill (read `.claude/skills/pytest/SKILL.md`).
2. For fixture patterns, read `.claude/skills/pytest/references/fixtures.md`.
   For mocking guidance, read `.claude/skills/pytest/references/mocking.md`.
3. For each acceptance criterion, draft the smallest test:
   - Name: `test_<behaviour>_when_<condition>`
   - Structure: AAA (Arrange-Act-Assert)
   - Every test file must set `pytestmark = pytest.mark.<marker>` at module level.
4. Show draft to user, wait for approval.
5. Write the test file(s).
6. Run `just test`. Classify the failure:

   | Failure type | Meaning | Action |
   |---|---|---|
   | `AssertionError` | Wrong behaviour | Ideal RED |
   | `AttributeError` / `ImportError` | Missing module/function | Good RED |
   | `SyntaxError` / `IndentationError` | Broken test | Fix test first |
   | `TypeError` (wrong signature) | Signature mismatch | Fix test first |
   | Unrelated exception | Regression | Investigate first |

7. Confirm RED: *"RED confirmed — failing for the right reason."*

Do not proceed until RED is confirmed for all acceptance criteria.

---

## Stage 2 — GREEN: Write minimal implementation

**Model:** Full (main model, interactive)

1. For each failing test, implement *just enough* to pass.
   - Include type annotations on all public functions.
   - If logging is involved, follow the structlog guidelines in `CLAUDE.md`
     (see "Structured logging" and "Mandatory `logging_manager` usage" sections).
2. Show draft, wait for approval.
3. Write implementation.
4. Run `just test`. All tests must pass.
5. Check coverage: `just coverage`. New code should be fully covered.
   - If coverage below 85%, write targeted tests for the uncovered lines
     visible in the `just coverage` output.
6. Confirm GREEN: *"GREEN confirmed — all tests pass."*

Do not proceed until GREEN is confirmed.

---

## Stage 3 — REFACTOR: Improve code quality

**Model:** Sonnet (Agent call)

Spawn an Agent with:
```
Load the python-docstrings skill (.claude/skills/python-docstrings/SKILL.md).

Review these files: {implementation_files}, {test_files}

Apply refactoring one group at a time:
- Naming and clarity
- Structure and duplication
- Docstrings (Google-style)
- Test improvements (parametrize, fixtures, naming)

Run `just test` after every change. If tests go red, revert immediately.

Report all changes applied.
```

Gate: all tests must stay green. No behaviour change.

---

## Stages 4, 5, 6 — Parallel quality checks

Launch 3 Agent calls simultaneously with `model: "haiku"`:

### Stage 4 — Code Quality Agent

```
Load the linting skill (.claude/skills/linting/SKILL.md) and type-checking skill
(.claude/skills/type-checking/SKILL.md).

Run: just fix && just fmt && just lint && just type

Fix any remaining violations. Gate: both exit 0.

Report: list of fixes applied.
```

### Stage 5 — Security Agent

```
Load the security skill (.claude/skills/security/SKILL.md).

Run security scans if configured:
- bandit -c pyproject.toml -r src/ (if bandit is available)
- semgrep --config .semgrep.yml src/ (if .semgrep.yml exists)

Review changed files for: hardcoded secrets, injection risks, unsafe patterns.
Fix findings or add justified suppressions with specific codes.

Report: findings and fixes.
```

### Stage 6 — Documentation Agent

```
Load the python-docstrings skill (.claude/skills/python-docstrings/SKILL.md)
and markdown skill (.claude/skills/markdown/SKILL.md).

Run: just docs-check

Verify all new public symbols have Google-style docstrings.
Update any affected markdown documentation in docs/.

Gate: just docs-check exits 0.

Report: docstrings added/fixed.
```

Wait for all 3 agents to complete before proceeding.

---

## Stage 7 — Git Commit

**Model:** Haiku (Agent call, sequential after stages 4-6)

```
1. Run `just ci` to verify everything passes.
2. If CI fails, classify the failure:
   - Test failure: read the error, fix the root cause
   - Lint violation: run `just fix` then `just lint`
   - Type error: fix the annotation or add a typed ignore with code
   - Import error: check dependency or module path
   - Coverage drop: add targeted tests
   Fix in priority order. Max 3 iterations.
3. Stage changed files: `git add <specific files>` (never git add -A).
4. Compose commit message:
   - Format: <type>: <imperative description>
   - Types: feat, fix, refactor, docs, test, chore, perf, ci, build
   - Subject line <= 72 characters, imperative mood
   - Body: explain WHY, list acceptance criteria covered
   - Footer: Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
5. Run `git commit`.
6. Gate: commit succeeds (pre-commit hooks pass).

Report: commit hash and message.
```

---

## Stage 8 — Pull Request

**Model:** Haiku (Agent call, sequential after stage 7)

```
Load the prepare_pr skill (.claude/skills/prepare_pr/SKILL.md).

1. Read .github/PULL_REQUEST_TEMPLATE.md (if exists).
2. Extract signals from commits: git log main..HEAD, git diff main...HEAD --stat.
3. Fill all PR template sections per the skill's rules.
4. Run: gh pr create --title "<title>" --body "<body>"
5. Output the PR URL.

Report: PR URL and title.
```

---

## Error handling

| Stage | On failure |
|---|---|
| 1-2 (RED/GREEN) | Stop pipeline. Report to user. Needs human judgment. |
| 3 (REFACTOR) | Stop. Revert changes. Report what went wrong. |
| 4-6 (parallel) | Each retries up to 3 times independently. Others continue. |
| 7 (COMMIT) | CI fix loop, max 3 iterations. Then stop + report. |
| 8 (PR) | Report error. Provide PR body for manual creation. |

---

## Multi-criterion features

When TASK.md has several acceptance criteria:
1. Run RED -> GREEN for each criterion in order.
2. Do not enter REFACTOR until all criteria have passing tests.
3. Extract shared fixtures to `conftest.py` during the second RED pass.

---

## Bug fix protocol

1. Write a test that reliably triggers the bug. Confirm RED.
2. Do not touch production code yet.
3. Fix the bug with the minimal change (GREEN).
4. Continue through REFACTOR -> VALIDATE as normal.

---

## Quick reference: where to go deeper

| Topic | Reference file |
|---|---|
| TASK.md format and validation | [references/task-template.md](references/task-template.md) |
| Stage banner format | [references/stage-banner.md](references/stage-banner.md) |

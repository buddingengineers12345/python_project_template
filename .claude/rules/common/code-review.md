# Code Review Standards

## When to review

Review your own code before every commit, and request a peer review before merging to
`main`. Self-review catches the majority of issues before CI runs.

**Mandatory review triggers:**
- Any change to security-sensitive code: authentication, authorisation, secret handling,
  user input processing.
- Architectural changes: new modules, changed public APIs, modified data models.
- Changes to CI/CD configuration or deployment scripts.
- Changes to `copier.yml` that affect generated projects.

## Self-review checklist

Before opening a PR, verify each item:

**Correctness**
- [ ] Code does what the requirement says.
- [ ] Edge cases are handled (empty inputs, None/null, boundary values).
- [ ] Error paths are covered by tests.

**Code quality**
- [ ] Functions are focused; no function exceeds 80 lines.
- [ ] No deep nesting (> 4 levels); use early returns instead.
- [ ] Variable and function names are clear and consistent with the codebase.
- [ ] No commented-out code left in.

**Testing**
- [ ] Every new public symbol has at least one test.
- [ ] `just coverage` shows no module below threshold.
- [ ] Tests are isolated and do not depend on order.

**Documentation**
- [ ] Every new public function/class/method has a Google-style docstring.
- [ ] `CLAUDE.md` is updated if project structure or commands changed.

**Security**
- [ ] No hardcoded secrets.
- [ ] No new external dependencies without justification.
- [ ] User inputs are validated.

**CI**
- [ ] `just ci` passes with zero errors locally before pushing.

## Severity levels

| Level | Meaning | Required action |
|-------|---------|-----------------|
| CRITICAL | Security vulnerability or data-loss risk | Block merge — must fix |
| HIGH | Bug or significant quality issue | Should fix before merge |
| MEDIUM | Maintainability or readability concern | Consider fixing |
| LOW | Style suggestion or minor improvement | Optional |

## Common issues to catch

| Issue | Example | Fix |
|-------|---------|-----|
| Large functions | > 80 lines | Extract helpers |
| Deep nesting | `if a: if b: if c:` | Early returns |
| Missing error handling | Bare `except:` | Handle specifically |
| Hardcoded magic values | `if status == 3:` | Named constant |
| Missing type annotations | `def foo(x):` | Add type hints |
| Missing docstring | No docstring on public function | Add Google-style docstring |
| Debug artefacts | `print("here")` | Remove or use logger |

## Integration with automated checks

The review checklist is enforced at multiple layers:

- **PostToolUse hooks**: ruff + basedpyright fire after every `.py` edit in a Claude session.
- **Pre-commit hooks**: ruff, basedpyright, secret scan on every `git commit`.
- **CI**: full `just ci` run on every push and pull request.

Fix violations at the earliest layer — it is cheaper to fix a ruff error immediately
after editing a file than to fix it after the CI pipeline fails.

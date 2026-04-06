# Code Review Standards

## Self-review checklist

**Correctness**
- [ ] Code does what the requirement says.
- [ ] Edge cases are handled (empty inputs, None/null, boundary values).
- [ ] Error paths are covered by tests.

**Code quality**
- [ ] Functions are focused; no function exceeds 80 lines.
- [ ] No deep nesting (> 4 levels); use early returns.
- [ ] No commented-out code.

**Testing**
- [ ] Every new public symbol has at least one test.
- [ ] `just coverage` shows no module below 85 %.
- [ ] Tests are isolated and order-independent.

**Documentation**
- [ ] Every new public function/class/method has a Google-style docstring.
- [ ] `CLAUDE.md` is updated if project structure or commands changed.

**Security**
- [ ] No hardcoded secrets.
- [ ] User inputs are validated.

**CI**
- [ ] `just ci` passes locally before pushing.

## Severity levels

| Level | Meaning | Action |
|-------|---------|--------|
| CRITICAL | Security vulnerability or data-loss risk | Block merge — must fix |
| HIGH | Bug or significant quality issue | Should fix before merge |
| MEDIUM | Maintainability concern | Consider fixing |
| LOW | Style suggestion | Optional |

## Automated enforcement

- **PostToolUse hooks**: ruff + basedpyright after every `.py` edit.
- **Pre-commit hooks**: ruff, basedpyright, secret scan on `git commit`.
- **CI**: full `just ci` on every push and pull request.

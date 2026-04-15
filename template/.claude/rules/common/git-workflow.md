# Git Workflow

- Commit format: `<type>: <imperative description>` (subject ≤ 72 chars). Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`, `build`.
- Never commit: hardcoded secrets, `*.rej` files, merge-conflict markers, debug statements.
- Blocked operations: `git commit --no-verify`, `git push --force`, direct push to `main`.
- Run `just review` before opening a PR; all CI checks must be green.

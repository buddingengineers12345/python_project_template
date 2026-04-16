---
name: security
description: >-
  Bandit, semgrep, and Python security patterns. Covers hardcoded secrets,
  injection risks, unsafe patterns, input validation, and cryptographic
  security. Use this skill when scanning for vulnerabilities, understanding
  security errors, or fixing security issues. Trigger on mentions of: security,
  vulnerability, bandit, semgrep, secret, API key, injection, SQL injection,
  command injection, or any request to audit code for security.
model: haiku
---

# Security Skill

Guidance for security scanning using **bandit** and **semgrep**, plus Python-specific
security patterns.

## Tool dispatch

| Tool | Command | When to use |
|---|---|---|
| Bandit | (configured if available) | General Python security issues |
| Semgrep | (configured if `.semgrep.yml` exists) | Pattern-based vulnerability scan |

## Manual security checklist

When reviewing code, check for:

| Category | What to check |
|---|---|
| Secrets | Hardcoded API keys, tokens, passwords, private keys in code or config |
| Input validation | All external inputs validated before use (CLI args, env vars, file paths, URLs) |
| Injection risks | SQL/command/code injection vectors; parameterized queries; no shell=True |
| Crypto | Use `secrets` module, never `random` for security-sensitive values |
| Path traversal | user_input validated against base directory; use `.resolve()` |
| Error handling | Error messages don't expose internal paths or config values |

## Efficiency: batch edits and parallel calls

- **Parallel calls:** Run `bandit` and `semgrep` scans in parallel as
  independent tool calls in a single message.
- **Batch edits:** When fixing multiple security findings in the same file,
  combine all fixes into a single Edit call.

## Quick reference: where to go deeper

| Topic                        | Reference file                                     |
|------------------------------|----------------------------------------------------|
| Bandit usage and rules       | [references/bandit.md](references/bandit.md)       |
| Semgrep usage and patterns   | [references/semgrep.md](references/semgrep.md)     |

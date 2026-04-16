# Rule categories

Copy-paste these templates into `.claude/rules/<category>.md` and adapt to your project.

---

## `code-style.md` — Code Style & Formatting

```markdown
# Code Style

- Indentation: 2 spaces (no tabs)
- Line length: max 100 characters
- Files must end with a newline
- No trailing whitespace

## Naming Conventions

- Variables/functions: camelCase
- Classes/types/interfaces: PascalCase
- Constants: SCREAMING_SNAKE_CASE
- Private class members: prefix with `_`
- React components: PascalCase filename matches export name

## Imports

- Order: external packages → internal absolute → relative paths
- Use path aliases (`@/`) for src-relative imports, not `../../`
- No barrel imports from `index.ts` unless the module explicitly provides one
- Group imports with a blank line between each group

## TypeScript

- Prefer `interface` over `type` for object shapes
- No `any` — use `unknown` and narrow, or `// eslint-disable` with justification comment
- All exported functions must have explicit return types
- Use strict null checks; handle `undefined` explicitly

## Formatting

- Run `npm run format` (Prettier) before committing
- ESLint config is in `.eslintrc.js`; fix all warnings before PR
```

---

## `testing.md` — Testing Conventions

```markdown
# Testing

## Commands

- Unit tests: `npm test`
- Integration tests: `npm run test:integration` (requires Docker via `docker-compose up -d`)
- Watch mode: `npm test -- --watch`
- Coverage: `npm run test:coverage` (target ≥ 80%)

## Patterns

- Use `describe`/`it` blocks, not `test()`
- Test file location: co-locate with source as `*.test.ts` OR in `tests/` for integration
- Import test utilities from `@/test-utils`, not directly from `@testing-library/react`
- Each `it` block tests exactly one behavior; no multiple assertions on unrelated things

## Mocking

- Mock all external services; never call real APIs, databases, or filesystems in unit tests
- Use `vi.mock()` (Vitest) or `jest.mock()` at the top of the file
- Shared mocks live in `tests/__mocks__/`
- Use `msw` (Mock Service Worker) for HTTP mocking in integration tests

## What to Test

- All exported functions in `src/lib/` must have unit tests
- React components: test behavior, not implementation (no snapshot tests)
- Error paths are as important as happy paths
- Don't test third-party library behavior
```

---

## `security.md` — Security Requirements

```markdown
---
paths:
  - "src/**/*.ts"
  - "src/**/*.tsx"
---

# Security Rules

## Secrets & Environment

- Never hardcode secrets, API keys, or tokens — use `process.env.VARIABLE_NAME`
- All env vars must be documented in `.env.example` (with placeholder values)
- Never log request bodies, headers containing auth tokens, or PII to console/logs
- Use `logger.redact(['password', 'token', 'secret'])` config in `src/lib/logger.ts`

## Input Validation

- Validate all user input with Zod schemas before processing
- Schema definitions live in `src/schemas/`; reuse existing schemas
- Sanitize HTML content with `DOMPurify` before rendering
- Use parameterized queries for all database operations (no string concatenation)

## Authentication & Authorization

- All API routes require auth unless decorated with `@PublicRoute`
- Use `requireRole(['admin'])` middleware from `src/middleware/auth.ts` for role checks
- JWT tokens expire in 15 minutes; use `refreshToken()` from `src/auth/client.ts`
- Never store tokens in `localStorage`; use httpOnly cookies

## Dependencies

- Run `npm audit` after adding dependencies; no high-severity vulnerabilities
- Pin direct dependencies to exact versions in `package.json`
```

---

## `git-workflow.md` — Git & PR Process

```markdown
# Git Workflow

## Branch Naming

- Features: `feat/<ticket-id>-short-description`
- Bugfixes: `fix/<ticket-id>-short-description`
- Chores: `chore/short-description`
- No pushing directly to `main` or `develop`

## Commit Messages

Follow Conventional Commits format:
```
<type>(<scope>): <short description>

[optional body]
[optional footer: BREAKING CHANGE or closes #issue]
```
Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`
Example: `feat(auth): add OAuth2 Google login`

## Before Committing

1. Run `npm run lint` — fix all errors
2. Run `npm test` — all tests must pass
3. Run `npm run format` — Prettier formatting
4. Stage only related changes — one logical change per commit

## Pull Requests

- PR title must match commit message format
- Link to Jira/Linear ticket in PR description
- Minimum 1 approval before merging
- Squash-merge to main; delete branch after merge
```

---

## `api-design.md` — API Conventions

```markdown
---
paths:
  - "src/api/**/*.ts"
  - "src/routes/**/*.ts"
---

# API Design Rules

## REST Conventions

- Use plural nouns for resources: `/users`, `/posts`, not `/user`, `/post`
- HTTP methods: GET (read), POST (create), PUT (replace), PATCH (update), DELETE (remove)
- Nest related resources max 2 levels: `/users/:id/posts` (not deeper)
- Return 201 for creation with `Location` header pointing to new resource

## Request & Response Format

- All request bodies validated with Zod schema before handler logic
- All responses use the standard envelope: `{ data: T, meta?: M, error?: E }`
- Error format: `{ error: { code: string, message: string, details?: unknown } }`
- Use the `ApiError` class from `src/lib/errors.ts` for all thrown errors

## Status Codes

- 200: Success (GET, PATCH, PUT)
- 201: Created (POST)
- 204: No content (DELETE)
- 400: Validation error / bad request
- 401: Unauthenticated
- 403: Unauthorized (authenticated but no permission)
- 404: Not found
- 409: Conflict (duplicate resource)
- 500: Unexpected server error (never expose stack traces)

## Documentation

- Add OpenAPI JSDoc comment to every handler export
- Use `@example` tags with realistic sample payloads
- Keep API docs in sync; run `npm run docs:api` to regenerate
```

---

## `architecture.md` — Architecture & Patterns

```markdown
# Architecture

## Module Structure

```
src/
├── api/          ← Route handlers only; no business logic
├── services/     ← Business logic; one service per domain
├── repositories/ ← Data access only; no business logic
├── lib/          ← Shared utilities with no domain knowledge
├── schemas/      ← Zod schemas; shared between API and services
└── types/        ← TypeScript types and interfaces
```

## Dependency Rules

- `api` → `services` → `repositories` (one direction only; no reverse imports)
- `lib` has no internal imports; only external packages
- No circular dependencies — enforced by `eslint-plugin-import`
- Use dependency injection; pass services as constructor params, not global singletons

## Patterns

- Repository pattern for all data access: never call DB client directly from services
- Service layer owns transactions: `await db.transaction(async (trx) => { ... })`
- Use `Result<T, E>` type from `src/lib/result.ts` for operations that can fail
- No `throw` in services; return `Result` and handle at the API layer

## Adding a New Feature

1. Define Zod schema in `src/schemas/`
2. Write repository method in `src/repositories/`
3. Write service method in `src/services/` (test it)
4. Write API handler in `src/api/` (test it)
5. Register route in `src/routes/index.ts`
```

---

## `documentation.md` — Documentation Standards

```markdown
# Documentation

## JSDoc

- All exported functions, classes, and types must have JSDoc
- Include `@param`, `@returns`, and `@throws` tags
- Use `@example` with a working code snippet for public APIs
- Don't document the obvious: `@param name - The name` adds no value

## README Standards

- Every package/app must have a README with: purpose, setup, usage, and env vars
- Keep setup steps executable (copy-paste commands that actually work)
- Update README when changing setup commands or env vars

## Comments in Code

- Comment *why*, not *what* — the code shows what; explain intent and trade-offs
- Use `// TODO(name): description` for tracked items (link to ticket when possible)
- Use `// NOTE:` for non-obvious behavior or important context
- Delete commented-out code; use git history instead

## Changelog

- Update `CHANGELOG.md` with every PR that changes user-facing behavior
- Follow Keep a Changelog format: Added / Changed / Deprecated / Removed / Fixed / Security
```

---

## `performance.md` — Performance Rules

```markdown
---
paths:
  - "src/**/*.ts"
  - "src/**/*.tsx"
---

# Performance

## Database

- All queries touching more than 1000 rows must be paginated
- Use `EXPLAIN ANALYZE` to check query plans for new queries on large tables
- Add database indexes for all foreign keys and columns used in WHERE clauses
- N+1 queries are prohibited: use `JOIN` or DataLoader batching

## Caching

- Cache expensive computations with `src/lib/cache.ts` (Redis-backed)
- Cache TTL defaults: session data 15min, reference data 1hr, static lookups 24hr
- Always invalidate cache on mutations: see `cache.invalidate(key)` pattern

## Frontend (if applicable)

- No synchronous work > 5ms on the main thread
- Lazy-load routes with `React.lazy()` and `Suspense`
- Images must use `next/image` (or equivalent) for automatic optimization
- Avoid re-renders: memoize expensive calculations with `useMemo`; stable callbacks with `useCallback`
```

---

## `workflow.md` — Development Workflow

```markdown
# Development Workflow

## Setup

```bash
git clone <repo>
cd <project>
cp .env.example .env.local    # Fill in your values
npm install
npm run db:migrate            # Apply DB migrations
npm run dev                   # Start dev server at http://localhost:3000
```

## Common Commands

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start dev server with hot reload |
| `npm run build` | Production build |
| `npm test` | Run unit tests |
| `npm run test:e2e` | Run E2E tests (requires dev server running) |
| `npm run lint` | Lint all files |
| `npm run format` | Format with Prettier |
| `npm run db:migrate` | Run pending migrations |
| `npm run db:seed` | Seed development database |
| `npm run typecheck` | TypeScript type check (no emit) |

## Environment Variables

Required vars are documented in `.env.example`. Do not commit `.env.local`.
Ask a teammate for the values of secrets prefixed with `SECRET_`.
```

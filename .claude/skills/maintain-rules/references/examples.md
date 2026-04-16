# Real-world example rules

Complete, copy-paste-ready example setups for common stacks.

---

## Next.js + TypeScript + Prisma

### `.claude/rules/code-style.md`
```markdown
# Code Style

- 2-space indentation; single quotes; semicolons required
- Prettier config in `.prettierrc`; run `pnpm format` before committing
- No `any`; use `unknown` and narrow, or `satisfies` operator
- Use `pnpm`, not `npm` or `yarn`

## File Organization

- Page components in `src/app/` (Next.js App Router)
- Shared components in `src/components/`; one component per file
- Server actions in `src/actions/`; prefix with `action` (e.g., `actionCreatePost`)
- Types in `src/types/`; no inline type definitions for reused types
```

### `.claude/rules/database.md`
```markdown
---
paths:
  - "src/lib/db/**/*"
  - "src/actions/**/*"
  - "prisma/**/*"
---

# Database Rules (Prisma)

- Never call `prisma` directly from components — use server actions or API routes
- All Prisma queries in `src/lib/db/` one file per model (e.g., `user.ts`, `post.ts`)
- Use `prisma.$transaction()` when multiple writes must be atomic
- New migrations: `pnpm prisma migrate dev --name <description>`
- After schema changes: run `pnpm prisma generate` to update the client
- Never use `prisma.user.deleteMany()` without a `where` clause
```

### `.claude/rules/testing.md`
```markdown
# Testing

- Test runner: Vitest (`pnpm test`)
- E2E: Playwright (`pnpm test:e2e`) — requires `pnpm dev` running in another terminal
- Unit test files: co-located as `*.test.ts`
- Mock Prisma using `vitest-mock-extended` and the mock in `tests/__mocks__/prisma.ts`
- Use React Testing Library for component tests; no Enzyme, no snapshot tests
```

---

## Python FastAPI + SQLAlchemy

### `.claude/rules/code-style.md`
```markdown
# Python Code Style

- Python 3.11+; use type annotations everywhere
- Black for formatting (`black .`); isort for imports (`isort .`)
- Max line length: 88 (Black default)
- Use `ruff` for linting: `ruff check .`

## Naming

- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private: prefix with `_`; avoid `__` name mangling unless necessary

## Type Hints

- All function signatures must be fully typed (params + return)
- Use `Optional[X]` only for Python <3.10; prefer `X | None` for 3.10+
- Use Pydantic models for all request/response schemas
```

### `.claude/rules/api.md`
```markdown
---
paths:
  - "src/routers/**/*.py"
  - "src/api/**/*.py"
---

# FastAPI Rules

- All routes must have Pydantic request/response models
- Use `Depends()` for all dependency injection (DB session, current user, etc.)
- Route handlers should be thin: validate input → call service → return response
- Business logic belongs in `src/services/`, not routers
- Use `HTTPException` with meaningful status codes and detail messages
- All routers tagged and included in `src/main.py` with prefix

## Database

- Never import `engine` directly; use `get_db` dependency from `src/database.py`
- Use `async with db.begin():` for transactions
- Raw SQL only via `text()` with bound parameters — no string interpolation
- Run migrations: `alembic upgrade head`
- New migration: `alembic revision --autogenerate -m "description"`
```

### `.claude/rules/testing.md`
```markdown
# Testing (Python)

- Framework: pytest with `pytest-asyncio` for async tests
- Run: `pytest` (unit) or `pytest tests/integration/` (integration, requires running DB)
- Coverage: `pytest --cov=src --cov-report=html` (target ≥ 80%)

## Patterns

- Use `pytest.fixture` for test setup; share in `conftest.py`
- Mock external services with `unittest.mock.patch` or `respx` for HTTP
- Database tests use `TestClient` with `override_dependencies` for in-memory SQLite
- One assertion concern per test; use descriptive test names: `test_create_user_returns_201`
```

---

## React Native + Expo

### `.claude/rules/code-style.md`
```markdown
# Code Style (React Native)

- TypeScript strict mode; no `any`
- StyleSheet.create() for all styles; no inline style objects
- Use `@/` path alias for src-relative imports (configured in tsconfig)
- Run `npx expo lint` before committing

## Component Patterns

- Functional components only; no class components
- Props interface named `<ComponentName>Props`; exported alongside component
- Use `forwardRef` when component wraps a native input element
- Keep components under 200 lines; extract sub-components to `components/` directory

## Platform Handling

- Use `Platform.select()` for platform-specific logic; avoid `Platform.OS === 'ios'` conditionals scattered in JSX
- Platform-specific files: `Component.ios.tsx` and `Component.android.tsx`
- Test on both platforms before marking a task done
```

### `.claude/rules/navigation.md`
```markdown
---
paths:
  - "src/navigation/**/*"
  - "src/screens/**/*"
---

# Navigation Rules (React Navigation)

- All screen names typed in `src/navigation/types.ts`
- Use typed `useNavigation<StackNavigationProp<...>>()` — never cast as any
- Navigate with `navigation.navigate('ScreenName', params)` not `push` (unless intentional stack duplication)
- Deep link routes registered in `src/navigation/linking.ts`
- Modal screens use separate `ModalStack`; don't mix with main stack
```

---

## Monorepo (Turborepo)

### Root `.claude/rules/monorepo.md`
```markdown
# Monorepo Rules (Turborepo)

## Commands

- Build all: `turbo build`
- Test all: `turbo test`
- Dev (all): `turbo dev`
- Dev (single): `turbo dev --filter=@acme/web`
- Add dependency to package: `pnpm add <dep> --filter=@acme/package-name`

## Package Structure

```
apps/
  web/        → Next.js customer app
  admin/      → Next.js admin app
  api/        → Express API server
packages/
  ui/         → Shared React component library
  config/     → Shared ESLint, TypeScript, Tailwind configs
  database/   → Prisma schema + generated client
  types/      → Shared TypeScript types
```

## Rules

- Shared code belongs in `packages/`, not duplicated across `apps/`
- Cross-package imports use package names (`@acme/ui`), not relative paths
- Never import from `apps/*` into `packages/*` (unidirectional dependency)
- Database schema changes need `pnpm prisma generate` run from `packages/database/`
- New package: copy the template from `packages/_template/`
```

---

## Minimal CLAUDE.md Starter Template

For a fresh project that doesn't have a CLAUDE.md yet:

```markdown
# [Project Name]

## About

[One sentence: what does this project do?]

## Tech Stack

- [Runtime/Language] + [Framework]
- [Database] with [ORM if any]
- [Testing framework]
- [Other key tools]

## Commands

| Command | Purpose |
|---------|---------|
| `[dev command]` | Start development |
| `[test command]` | Run tests |
| `[lint command]` | Lint code |
| `[build command]` | Build for production |

## Project Layout

```
src/
  [key directory]/ ← [what goes here]
  [key directory]/ ← [what goes here]
```

## Key Conventions

- [Most important convention specific to this project]
- [Second most important convention]
- [Package manager to use, e.g., "Use pnpm, not npm"]

## What NOT to Do

- [Common mistake this project has hit before]
- [Anti-pattern to avoid here]
```

Keep CLAUDE.md under 200 lines. Move detailed rules to `.claude/rules/`.
```

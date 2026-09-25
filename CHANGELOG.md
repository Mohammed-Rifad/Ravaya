# Changelog

## Day 2 — Phase 0: frontend foundation
- Next.js 16 (App Router), React 19, TypeScript strict (+ extra checks), Tailwind v4.
- Prettier (with Tailwind class sorting), ESLint + eslint-config-prettier, `--max-warnings=0`.
- npm scripts: lint, typecheck, format, format:check. Node 24 pinned (engines, .npmrc, .nvmrc).
- `lib/env.ts` validates `NEXT_PUBLIC_API_URL`; `lib/api.ts` returns `Result<T>`, never throws.
- Home page checks `/api/health/` per request; loading, error and success states.

## Day 1 — Phase 0: backend foundation
- Django 5.2 LTS + DRF; settings split into base/dev/test/prod; config from `.env`.
- Neon Postgres (direct connection); pgvector enabled by migration.
- Custom User: UUID id, email login, lowercased + case-insensitive unique.
- `GET /api/health/` with a database round-trip; one JSON error envelope for all errors.
- pytest (11 tests), black, ruff.

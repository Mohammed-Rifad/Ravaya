# Deployment

Managed services, not a hand-built server. EC2 + Nginx + Gunicorn is unnecessary cost and
maintenance for this project.

| Piece | Service | Notes |
|---|---|---|
| Frontend | Vercel | Connect the repo; `frontend/` as root; `ravaya.<tld>` |
| Backend | Railway or Render | Docker or buildpack; auto-deploy from `main`; `api.ravaya.<tld>` |
| Database | Neon | Postgres 16; enable `vector`. `main` branch = production, `dev` branch = local development |
| Images | Cloudinary or Supabase Storage | Never commit images to the repo |
| Errors | Sentry | Both frontend and backend |
| Cron | Railway/Render scheduled jobs | `release_expired_orders` every 10 min; nightly `seed_demo --reset` |
| Domain | Any registrar (~USD 10/year) | Required before Phase 4 |

All hosting has free tiers sufficient for a portfolio demo; the domain is the only cost.

## Why a custom domain

Auth and guest carts rely on cookies set by the API. On `*.vercel.app` + `*.railway.app`
those are third-party cookies and browsers block them. On `ravaya.<tld>` +
`api.ravaya.<tld>` they are same-site and work everywhere. Phases 0–3 can run on the
default platform hosts; attach the domain before Phase 4. See `docs/architecture.md`.

## First deploy (Phase 0)

1. Create the Neon project (Postgres 16). The first migration runs
   `CREATE EXTENSION IF NOT EXISTS vector;`.
2. Deploy the backend; set env vars; run `migrate`. Confirm `/api/health/` returns `ok`.
3. Deploy the frontend with `NEXT_PUBLIC_API_URL` pointing at the backend.
4. Set `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` to the real hosts.

From Phase 2: run `seed_demo` after migrating. From Phase 12: then `embed_products`.

## Attaching the domain (before Phase 4)

1. Point `ravaya.<tld>` at Vercel and `api.ravaya.<tld>` at the backend.
2. Set `NEXT_PUBLIC_API_URL=https://api.ravaya.<tld>/api`, `ALLOWED_HOSTS`,
   `CORS_ALLOWED_ORIGINS=https://ravaya.<tld>`, `CSRF_TRUSTED_ORIGINS`, and
   `AUTH_COOKIE_DOMAIN=.ravaya.<tld>`.
3. Confirm HTTPS on both, then log in on Safari and reload — the session must survive.

## Production checklist

- [ ] `DEBUG=False`, real `DJANGO_SECRET_KEY`
- [ ] `ALLOWED_HOSTS`, CORS and `CSRF_TRUSTED_ORIGINS` restricted to your domains
- [ ] Secure cookies: `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SameSite=Lax`
- [ ] Client IP read from the platform's `X-Forwarded-For` (one trusted hop) so rate
      limits see real users
- [ ] Database backups enabled
- [ ] Sentry receiving events from both sides
- [ ] Rate limits live on `/api/auth/*`, `/api/orders/track/` and `/api/ai/*`
- [ ] AI daily spend ceiling and token prices configured
- [ ] `release_expired_orders` and nightly demo reset scheduled and verified
- [ ] "Demo store — no real orders are processed" badge visible
- [ ] Sitemap and robots.txt served correctly
- [ ] Lighthouse mobile run recorded in the README

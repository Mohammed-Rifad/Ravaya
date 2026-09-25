# Architecture

```
Browser
  │
  ├── Next.js (Vercel)  ravaya.example
  │     server components render public pages, fetching the API directly
  │     client components handle auth-bound pages, cart, chat, filters
  │
  └── Django + DRF (Railway/Render)  api.ravaya.example
        ├── views      thin: auth, validation, serialization
        ├── services   all business logic
        ├── models     data + constraints
        └── ai/        AIService, tool registry, validators
              │
              ├── Gemini (chat + embeddings)
              └── PostgreSQL + pgvector (Neon/Supabase)
```

**Rule:** views never contain business logic. A view authenticates, validates, calls a
service, and serializes the result.

## Domains and cookies

The frontend and API live on **one registrable domain**: `ravaya.example` and
`api.ravaya.example`. Cross-origin, but **same-site**, so the refresh cookie and the guest
cart cookie are first-party and survive Safari ITP and third-party-cookie blocking.
Two unrelated hosts (`*.vercel.app` + `*.railway.app`) would make them third-party
cookies and break login and guest carts.

- Local development: `localhost:3000` and `localhost:8000` are already same-site.
- Vercel preview deployments on `*.vercel.app` can browse the catalogue but cannot log in.
  That is accepted.
- Browser → API calls use `credentials: "include"`; CORS allows credentials for the
  frontend origin only.

## Request flow — adding to cart

```
POST /api/cart/items/ {variant_id, quantity}
  → serializer validates shape
  → CartService.add_item()
      → loads the variant, checks is_active
      → checks stock; clamps or rejects with a clear error
      → upserts the cart item
      → recomputes subtotal, discount, shipping, VAT, total
  → returns the whole cart
```
The client renders what it is given. It never computes money. Adding to the cart does not
reserve stock; stock is taken at order creation (see `docs/database.md`).

## Folder structure

```
ravaya/
├── .github/workflows/  ci.yml (lint + offline tests), ai-evals.yml (live evals)
├── frontend/
│   ├── app/            [locale]/ with (shop)/ (account)/ (admin)/ ai/
│   ├── components/     ui/ product/ cart/ ai/ layout/
│   ├── features/       cart/ checkout/ ai-chat/
│   ├── lib/            api client, formatters, i18n
│   ├── messages/       en.json  ar.json
│   └── types/
├── backend/
│   ├── config/         settings/{base,dev,prod}.py, urls.py
│   ├── apps/
│   │   ├── users/ products/ cart/ orders/ payments/
│   │   ├── coupons/ wishlist/ reviews/ ai/ core/
│   │   └── each: models.py serializers.py views.py services.py tests/
│   ├── tests/          cross-cutting suites: security/ (ownership), ai/ (guardrails, evals)
│   └── manage.py
├── docs/
├── .env.example
├── CLAUDE.md
└── README.md
```

## Cross-cutting decisions

- **Auth:** SimpleJWT. Short-lived access token in browser memory, refresh token in an
  httpOnly, `Secure`, `SameSite=Lax` cookie scoped to `/api/auth/`. Never store tokens in
  localStorage. Refresh and logout also require Django's CSRF token. The Next.js server
  never holds a user's token, so auth-bound pages are client components.
- **Guest carts:** identified by the Django session cookie (same-site, httpOnly). On login
  the session cart merges into the user cart.
- **Money:** Decimal throughout, computed server-side, VAT-inclusive display.
- **Stock:** decremented atomically at order creation; released on cancellation or
  payment failure. See `docs/database.md`.
- **i18n:** `next-intl`, `en` + `ar`, locale-prefixed routes (`/en/...`, `/ar/...`), `dir`
  switched at the layout level, `hreflang` alternates on every page.
- **Images:** Next.js image optimisation; one primary image per product; alt text in both
  languages.
- **Errors:** one error envelope everywhere; Sentry on both sides.
- **Caching:** category and product list responses cached briefly; embeddings cached by hash.
- **Client IP:** taken from `X-Forwarded-For` as set by the hosting platform's proxy (trust
  exactly one hop). Used for rate limiting.

# Build Plan

17 phases. Ship and deploy after each one. Do not begin a phase while the previous
phase has failing tests.

**Client-demo milestone:** after Phase 3 you have a beautiful working storefront. That is
enough to show prospective website clients. Everything after that is for the portfolio.

---

## Phase 0 — Foundations

Repository, tooling and the decisions that are painful to change later.

- Monorepo (git, `main` branch, pushed to GitHub): `frontend/`, `backend/`, `docs/`.
  `.gitignore` covers `.env`, `.env.local`, `.venv/`, `node_modules/`, `.next/`.
- Django project + DRF + Postgres (first migration enables `vector`). The custom `User`
  model exists before the first `migrate` — swapping it later forces a database reset.
- Next.js + TypeScript (`strict`) + Tailwind.
- Root `.env.example` documents both sides. Nothing secret committed.
- `black`, `ruff`, `eslint`, `prettier` configured.
- pytest + pytest-django running with one trivial test; `live` marker registered and
  excluded by default.
- CI: GitHub Actions `ci.yml` running lint + offline tests + `npm run build` on push.
- Sentry wired into both frontend and backend.
- `GET /api/health/` returning `{"status": "ok"}` after a database round-trip.
- **Decide and record in `docs/decisions.md`:** product image source and shooting/selection
  standard (see "Images" below), and the production domain (see `docs/deployment.md`).

**Done when:** CI is green, an empty Next.js page is live on Vercel, and the backend is
live on Railway/Render with `/api/health/` returning `ok` against the hosted database.
Every later phase deploys to these same environments.

### Images — decide now, not in Phase 2
30 products × 3 images = 90 images that must look like one brand. Mixed sources will
undermine the entire project. Choose one:
- **(a)** Photograph real bottles yourself: one backdrop, one light source, one angle set.
- **(b)** One photographer's collection from a stock library, filtered for consistency.

Write the choice, the image dimensions, and the naming convention into `docs/decisions.md`.

---

## Phase 1 — Design system + i18n

The visual foundation and the language layer, together. Arabic added later is a rewrite.

- Design tokens: colour, type scale, spacing, radius, shadow.
- Typography: one serif for display, one sans for UI, plus an Arabic family (Tajawal or
  Noto Kufi Arabic). Latin and Arabic sizes tuned separately.
- Components: Button, Input, Select, Card, Badge, Modal, Drawer, Toast, Skeleton.
- Navbar (with search, wishlist, cart, account, language switch) and Footer.
- `next-intl` configured; `en` and `ar` message files; `dir="rtl"` handling.
- Mobile-first. Test at 320 / 375 / 390 / 414 / 768 / 1024 / 1280.

**Avoid:** generic SaaS dashboard styling, neon gradients, heavy glassmorphism, animation
on everything. The identity is luxury + Arabian heritage + restraint.

**Done when:** a component gallery page renders every component in both languages, and
switching to Arabic flips the layout correctly.

---

## Phase 2 — Database + demo catalogue

- All models from `docs/database.md`, with constraints and indexes.
- `seed_demo` management command creating the 30 products with variants, images, notes and
  all fragrance attributes.
- `seed_demo --reset` clearing test orders and restoring the catalogue.
- Model tests: constraints hold, slugs are unique, stock cannot go negative.

**Done when:** `python manage.py seed_demo` produces 30 complete products and the admin can
list them.

---

## Phase 3 — Storefront  ← client-demo milestone

- Home: hero, new arrivals, best sellers, oud collection, gift sets, brand story,
  testimonials (labelled as demo), newsletter.
- Shop: filters (category, price, gender, family, occasion, season, intensity,
  availability), sorting, pagination. Never load the full catalogue at once.
- Category pages, product detail page with gallery, variant selector, fragrance profile,
  notes pyramid, "complete your scent".
- Keyword search across name, description, SKU, family, notes.
- SEO: metadata, Open Graph, sitemap (both locales), robots.txt, slug URLs, image alt
  text, `hreflang` alternates between `/en/` and `/ar/`.

**Done when:** a stranger can browse the whole catalogue on a phone and it feels like a
real shop. Screenshot it — this is your client demo.

---

## Phase 4 — Authentication

- **Prerequisite:** the production custom domain is live (`ravaya.<tld>` on Vercel,
  `api.ravaya.<tld>` on the backend). Auth cookies do not work across `*.vercel.app` and
  `*.railway.app`. See `docs/architecture.md`.
- Register, login, logout, refresh. SimpleJWT, refresh token in an httpOnly, `Secure`,
  `SameSite=Lax` cookie; refresh rotation with blacklist; CSRF on refresh and logout.
- Rate limits on `/api/auth/*` (5/min per IP).
- Profile, addresses (CRUD, default address).
- Route protection on both sides; permissions enforced in DRF, never in the UI only.
  Account pages are client components (the Next.js server never holds the token).
- **Guest checkout is supported.** Account creation is optional and offered after purchase.
- Anonymous cart merges into the user cart on login.

**Done when:** the ownership test passes — Customer A requesting Customer B's address or
order receives 404, never data — and login survives a page reload in Safari on the live
domain.

---

## Phase 5 — Cart + wishlist

- Cart with variant selection, quantity, coupon, subtotal, shipping, VAT, total.
- **Server-side stock validation.** Ordering 10 when 3 exist is rejected or clamped, with a
  clear message.
- Wishlist: add, remove, view, move to cart. Persisted for authenticated users.
  *(Optional — cut first if time is short.)*

**Done when:** every total is recomputed server-side and a tampered client payload changes
nothing.

---

## Phase 6 — Checkout + orders

- Mobile-first checkout: name, email, phone (+966 validated), address, city, district,
  postal code, delivery notes.
- Order creation with **snapshots** of product name, SKU, variant, price, quantity.
- Order number from a Postgres sequence: `RAV-2026-00124`. Never a UUID shown to customers.
- VAT stored on the order. Order history and order detail pages.
- Statuses: Pending, Confirmed, Processing, Shipped, Delivered, Cancelled — transitions
  enforced by `OrderService` per the lifecycle in `docs/database.md`.
- **Stock taken and coupon consumed atomically** at order creation; both returned on
  cancellation. Customer can cancel while pending or confirmed.
- Guest order tracking by order number + email, rate limited.

**Done when:** editing a product afterwards does not alter any historical order, and a
concurrency test (two simultaneous orders for the last unit) produces exactly one order.

---

## Phase 7 — Admin

- Custom dashboard (not Django Admin alone): sales, orders, customers, products, low stock.
- Charts: sales trend, orders trend, top products, category performance.
- Product management: create, edit, publish/unpublish, images, variants, stock, prices,
  fragrance attributes.
- Order management: search, filter, open, update status, cancel, and for COD orders
  "delivered, cash collected".
- Coupons: percentage, fixed, minimum order, expiry, usage limit, active flag.
- Reviews *(optional)*: customers submit from the product page; verified-purchase flag set
  from delivered orders; staff moderation queue; only approved reviews count.

**Done when:** you can run the entire shop without touching the database or Django Admin.

---

## Phase 8 — Payments

- `PaymentService` interface: `create_payment`, `verify_payment`, `handle_webhook`,
  `refund_payment`.
- Mock provider modelling **mada, Apple Pay, card and COD**.
- Payment statuses: Pending, Paid, Failed, Refunded.
- Webhook endpoint with signature verification (mocked, but implemented as if real) and
  idempotency (a replayed webhook changes nothing).
- Provider swappable via configuration, not code changes.
- COD follows its own lifecycle (paid only on the staff "cash collected" action).
- `release_expired_orders` scheduled every 10 minutes: cancels unpaid online orders past
  `payment_due_at` and returns their stock.

**Done when:** a forged "payment succeeded" request from the frontend does not mark an
order paid, and an abandoned online order releases its stock after the hold period.

---

## Phase 9 — AI foundation

- `AIService`, Gemini integration, prompt architecture, tool registry.
- Tool argument validation layer. `AIConversation` and `AIMessage` models.
- **Rate limiting** on `/api/ai/*`: 10/min per IP, 100/day per session.
- **Token cap per request** and a **daily spend ceiling** (priced from env), failing
  closed with a clear message.
- **Offline guardrail tests**: `backend/tests/ai/test_guardrails.py` with a fake model,
  run on every push.
- **Live eval harness**: `backend/tests/ai/test_evals.py` with 40 golden cases, including
  adversarial ones (prompt injection, another customer's order, requests for invented
  products). Runs via `ai-evals.yml`: nightly, on manual dispatch, and on PRs that touch
  prompts or tools.

**Done when:** the guardrail tests pass on every push, the live suite runs in CI, and every
adversarial case is handled safely (10/10).

---

## Phase 10 — AI Fragrance Consultant

"Find My Signature Scent." Natural conversation, preference extraction, clarifying
questions, real product recommendations rendered as cards with View Product and Add to Cart.

**Done when:** every recommended product exists in the database and every price matches it.

---

## Phase 11 — AI natural-language search

`POST /api/ai/search/` — the model converts text into structured filters, a serializer
validates them, Django runs the query.

**Done when:** "fresh perfume for summer under SAR 300" returns correct results and the
model never produces SQL.

---

## Phase 12 — Recommendations + pgvector

- Level 1: structured similarity (category, family, notes, occasion, season, mood, price).
- Level 2: pgvector embeddings of a composed product document (`gemini-embedding-2`,
  768 dims, normalised, HNSW cosine index).
- Embeddings cached; regenerated only when embedded fields change.

**Done when:** similar products are genuinely similar and re-running the embed command
re-embeds nothing.

---

## Phase 13 — Gift Finder

Recipient, gender, occasion, budget, product type, fragrance style → real products →
Add Gift to Cart.

---

## Phase 14 — Comparison + support assistant

- Compare two or more fragrances on a fixed set of attributes. Never invent a value.
- Support assistant: products, notes, shipping, returns, payment, policies, order status.
- "Where is my order?" uses `get_customer_orders`, scoped to the authenticated user only.

---

## Phase 15 — Security, SEO, performance

- Full permission audit: every endpoint, every object.
- Rate limiting across auth and AI endpoints.
- Indexes and query optimisation; no N+1 queries.
- Core Web Vitals; image optimisation; pagination everywhere.
- Canonical URLs, structured metadata, sitemap regeneration.

---

## Phase 16 — Testing + deployment

- Unit, API, security and AI eval tests all green in CI.
- Mobile testing on a real device, not just a resized browser.
- Production hardening of the environments live since Phase 0: work through the
  production checklist in `docs/deployment.md`.
- Nightly `seed_demo --reset` cron so the public demo stays clean.
- "Demo store — no real orders are processed" badge visible.
- README with screenshots, architecture diagram and a 90-second demo video.

---

## Priority if time runs short

**Must have:** premium UI · catalogue · product detail · search and filter · cart ·
checkout · orders · auth · admin · AI consultant

**High value:** natural-language search · recommendations · pgvector · gift finder ·
comparison

**Optional:** reviews (Phase 7) · wishlist (Phase 5) · advanced analytics

**Later:** voice, loyalty, subscriptions, ERP, warehouse, shipping automation

# Decision Log

One entry per decision that would be expensive to reverse. Keep it short.
Rows dated "≤ 2026-09-25" were taken in the original plan, before the log was dated.

| Date | Decision | Why | Alternatives rejected |
|---|---|---|---|
| ≤ 2026-09-25 | Prices are VAT-inclusive at 15% | Saudi consumer expectation | VAT added at checkout |
| ≤ 2026-09-25 | Guest checkout allowed | Forced registration kills conversion | Account required |
| ≤ 2026-09-25 | Money as Decimal(10,2) | Float rounding errors are unacceptable | Float, integer halalas |
| ≤ 2026-09-25 | Order numbers from a Postgres sequence | MAX+1 races under load | UUID shown to customers |
| ≤ 2026-09-25 | Managed hosting, not EC2 | Cost and maintenance | EC2 + Nginx + Gunicorn |
| 2026-09-25 | Frontend and API on one registrable domain (`ravaya.<tld>` + `api.ravaya.<tld>`) | Refresh and guest-cart cookies stay same-site; third-party cookie blocking would break auth on platform hosts | Proxying `/api` through Next.js (hides client IP from rate limiting, extra hop, streaming quirks); tokens in localStorage (XSS exposure) |
| 2026-09-25 | Auth-bound pages are client components; server components render public pages only | Access token lives in browser memory; the Next.js server never holds it | Server-side session in Next.js (a second auth system) |
| 2026-09-25 | Stock taken atomically at order creation, returned on cancellation; unpaid online orders cancelled after `PAYMENT_HOLD_MINUTES` (30) | Prevents overselling the last unit; abandoned payments don't lock stock forever | Reserve at add-to-cart (stock locked by browsers); decrement on payment (oversells during payment) |
| 2026-09-25 | COD orders confirmed at creation; marked paid only by the staff "cash collected" action | Keeps "paid only when verified server-side" true for COD | Marking COD paid at creation |
| 2026-09-25 | Coupon usage consumed with a conditional `UPDATE` at order creation | `used_count` read-then-write races past `usage_limit` | Counting `CouponUsage` rows at validation time |
| 2026-09-25 | Embeddings: `gemini-embedding-2`, 768 dims, normalised; HNSW cosine index | `text-embedding-004` was shut down 2026-01-14; model is multilingual (Arabic); IVFFlat needs training data and is pointless at 30 rows | `gemini-embedding-001` (text-only legacy); 3072 dims (storage for no gain at this scale) |
| 2026-09-25 | Chat model `gemini-3.8-flash`, thinking level low, set via env | Current GA Flash model; low thinking keeps latency and cost down for tool calling | Hard-coding a model name |
| 2026-09-25 | AI tests split: offline guardrail tests on every push, live evals nightly / on prompt PRs / manual | Live calls cost money, need a key and are non-deterministic; guardrails are enforced by code and testable offline | All 40 live evals on every push |
| 2026-09-25 | Guest order tracking requires order number **and** email, POST, rate limited | Sequential order numbers are guessable | Order number + phone via GET |
| 2026-09-25 | Page URLs use slugs/order numbers; API payloads may use opaque UUIDs | Clarifies the "never expose an ID" rule without contorting the cart and address APIs | Slugs for every API object |
| 2026-09-25 | Product images from **one photographer's collection on a stock library** (Unsplash/Pexels), filtered for one backdrop, light and angle | Faster than a shoot; a single photographer keeps the set consistent | Own photography (days of shooting); mixed sources (inconsistent brand) |
| 2026-09-25 | Local development uses a Neon `dev` branch, not a local Postgres | No Postgres or Docker installed; pgvector included; same engine as production | Local Postgres 16 (pgvector build on Windows); Docker Desktop |
| 2026-09-25 | Node 24 LTS | Node 20 is end-of-life (April 2026); matches Vercel's default | Staying on Node 20 |
| 2026-09-25 | Django 5.2 LTS | Long-term support to April 2028 | Django 6.0 (shorter support window) |
| 2026-09-25 | Email uniqueness: stored lowercased, `unique`, plus a `CHECK (email = lower(email))` — no `citext` | Django removed its citext fields in 5.1; `USERNAME_FIELD` must be a plain unique field | `citext` extension; functional unique index on `Lower(email)` (fails Django's auth check) |
| 2026-09-25 | Custom `User` model created in Phase 0 | Swapping the user model after the first `migrate` forces a database reset | Creating it in Phase 2 |
| 2026-09-25 | Neon **direct** connection (no pooler) for dev, tests and prod | The pooler holds connections open, blocking test-database teardown; long-running Django pools its own via `CONN_MAX_AGE` | Neon pooled endpoint |
| 2026-09-25 | Next.js 16.3 + React 19.2 + Tailwind v4 (CSS-first config) | Current stable versions; v4 needs no `tailwind.config.js` | Tailwind v3 |
| 2026-09-25 | API client returns `Result<T>` instead of throwing | TypeScript forces every page to handle the error state (rule 9) | try/catch at every call site |

**Image standard (fill in on Day 3):** photographer ____ · dimensions 1600×2000 (4:5),
WebP, neutral backdrop · naming `{product-slug}-{1..3}.webp`, `-1` is the primary image.

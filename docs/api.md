# API

Base: `https://api.<domain>/api/` (dev: `http://localhost:8000/api/`). JSON only. DRF
serializers validate every input.
Auth: `Authorization: Bearer <access>`; refresh token in an httpOnly cookie.
Browser requests are sent with `credentials: "include"` (guest cart session cookie).
Pagination: `?page=&page_size=` (default 24, max 60).

Errors are consistent:
```json
{ "error": { "code": "out_of_stock", "message": "Only 3 left in stock.", "field": "quantity" } }
```
`code`, `message` and `field` describe the first error (`field` is `null` when the error
is not about one field; nested fields use a dotted path such as `address.city`).
Validation errors (`400`) also carry `details`: every field error, keyed by field, so a
form can mark all invalid inputs at once. Implemented in `apps/core/exceptions.py`.
Rate-limited responses are `429` with `code: "rate_limited"` and a `Retry-After` header.

**Identifiers:** pages link by slug or order number. Cart items, addresses, variants and
wishlist items are referenced in the API by opaque UUIDs. Every object lookup is scoped to
the caller (`request.user` or the session); a miss and a foreign object both return `404`.

---

## Auth  (rate limited: 5/min per IP on register, login, refresh)
```
POST   /api/auth/register/        {email, password, full_name, phone}
POST   /api/auth/login/           {email, password}  -> {access, user}   sets refresh cookie
POST   /api/auth/refresh/         (cookie + CSRF)    -> {access}          rotates refresh cookie
POST   /api/auth/logout/          (cookie + CSRF)                         blacklists refresh
GET    /api/auth/csrf/                                                    sets CSRF cookie
GET    /api/auth/me/
PATCH  /api/auth/me/              {full_name, phone}
```
Login merges the session cart into the user cart server-side; there is no separate merge
call.

## Catalogue (public)
```
GET /api/products/?category=&family=&gender=&occasion=&season=&intensity=
                  &min_price=&max_price=&in_stock=&on_sale=&sort=&search=&page=
GET /api/products/{slug}/
GET /api/products/{slug}/related/
GET /api/categories/
GET /api/categories/{slug}/
GET /api/notes/
```
`sort`: `featured | newest | bestselling | price_asc | price_desc`
`category` takes a category slug (`perfumes`, `oud`, …). Unknown filter values are `400`.

## Cart
```
GET    /api/cart/
POST   /api/cart/items/        {variant_id, quantity}
PATCH  /api/cart/items/{id}/   {quantity}
DELETE /api/cart/items/{id}/
POST   /api/cart/coupon/       {code}
DELETE /api/cart/coupon/
```
Every response returns fully recomputed totals: subtotal, discount, shipping, vat_amount,
total. The client never calculates money. Anonymous carts use the session cookie; unsafe
methods on cookie-identified carts require the CSRF token.

## Orders
```
POST /api/orders/          {contact, address, payment_method, notes}  -> {order_no, payment}
GET  /api/orders/                        (authenticated: own orders only)
GET  /api/orders/{order_no}/             (owner or staff only)
POST /api/orders/{order_no}/cancel/      (owner, while status is pending or confirmed)
POST /api/orders/track/    {order_no, email}   guest tracking
```
`POST /api/orders/` takes stock and consumes the coupon atomically (see
`docs/database.md`); it fails with `out_of_stock` or `coupon_exhausted` and creates nothing.

**Guest tracking** requires the order number **and** the email on the order (exact,
case-insensitive). It is a POST so the email never appears in URLs or logs. Rate limited
to 5/min per IP. A wrong email and a nonexistent order return the same `404`. The response
omits the street address and phone.

## Payments
```
POST /api/payments/create/     {order_no}                  online methods only
POST /api/payments/verify/     {order_no, provider_ref}    server asks the provider
POST /api/payments/webhook/    provider -> us, signature verified, idempotent
```
An order becomes `paid` only via `verify`, the webhook, or — for COD — the staff
"delivered, cash collected" action. Never from a client claim.

## Account
```
GET|POST         /api/addresses/
GET|PATCH|DELETE /api/addresses/{id}/
GET              /api/wishlist/
POST             /api/wishlist/items/   {product_slug}
DELETE           /api/wishlist/items/{id}/
POST             /api/wishlist/items/{id}/move-to-cart/   {variant_id}
POST             /api/reviews/          {product_slug, rating, comment}
```

## AI  (rate limited: 10/min per IP, 100/day per user or session; daily spend ceiling)
```
POST /api/ai/chat/        {conversation_id?, message}
POST /api/ai/search/      {query}
POST /api/ai/recommend/   {product_slug?, preferences?}
POST /api/ai/compare/     {slugs: [..]}
POST /api/ai/gift/        {recipient, occasion, budget, notes?}
```
Chat responses stream as Server-Sent Events (`text/event-stream`, via Django
`StreamingHttpResponse`; run gunicorn with threaded workers) and end with a structured
payload of product cards:
```json
{ "message": "...", "products": [ {slug, name, price, family, image, key_notes} ] }
```
When the spend ceiling is reached: `503` with `code: "ai_unavailable"` and a clear message.

## Admin  (staff only, enforced server-side)
```
GET    /api/admin/stats/
GET    /api/admin/products/          POST /api/admin/products/
PATCH  /api/admin/products/{id}/     DELETE /api/admin/products/{id}/
POST   /api/admin/products/{id}/images/
PATCH  /api/admin/variants/{id}/     stock and price
GET    /api/admin/orders/            ?status=&search=&from=&to=
PATCH  /api/admin/orders/{id}/       {status}
POST   /api/admin/orders/{id}/cod-collected/     COD: delivered + paid
POST   /api/admin/orders/{id}/refund/
GET    /api/admin/customers/
GET|POST|PATCH /api/admin/coupons/
POST   /api/admin/reviews/{id}/approve/
```
Order status changes go through `OrderService`, which rejects illegal transitions (see the
lifecycle in `docs/database.md`) and returns stock on cancellation.

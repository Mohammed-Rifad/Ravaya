# Database

PostgreSQL 16 with the `vector` extension, enabled in the first migration
(`apps/core/migrations/0001_enable_extensions.py`). All money is
`DecimalField(max_digits=10, decimal_places=2)` — never float. All timestamps are
timezone-aware UTC.

Page URLs use **slugs** and **order numbers**. UUIDs are opaque identifiers in API
payloads only; they never appear in a page URL.

---

## Money and VAT

Saudi VAT is **15%** and displayed prices are **VAT-inclusive**, which is what Saudi
shoppers expect.

```
line_total   = unit_price * quantity          # VAT-inclusive
subtotal     = sum(line_total)
discount     = coupon applied to subtotal, capped at max_discount and at subtotal
shipping     = STORE_FLAT_SHIPPING, or 0 when subtotal - discount >= STORE_FREE_SHIPPING_ABOVE
total        = subtotal - discount + shipping
vat_amount   = round(total * vat_rate / (100 + vat_rate), 2)   # VAT contained in total
```

`vat_rate` comes from `STORE_VAT_RATE` (15.00) and is stored on the order so historical
orders survive a rate change. Round with `ROUND_HALF_UP`. Show "Includes VAT" next to the
total at checkout.

---

## Models

### User
Custom user, email as the login field.
```
id                UUID pk
email             varchar(254) unique   # always stored lowercased; check constraint
                                        # email = lower(email) makes unique case-insensitive
password          hashed
full_name         varchar(120)
phone             varchar(20)        # normalised +9665XXXXXXXX
is_staff          bool
is_active         bool
date_joined       timestamptz
```

### Address
```
id UUID, user_fk, label, full_name, phone, city, district,
street, postal_code, notes, is_default bool, created_at
```
Index: `(user_id, is_default)`. Only one default per user — enforce with a partial unique
index on `(user_id) WHERE is_default` and set it in the service.

### Category
```
id, name_en, name_ar, slug unique, description_en, description_ar,
image, parent_fk null, sort_order, is_active
```
Slugs are fixed: `perfumes`, `oud`, `attar`, `bakhoor`, `gift-sets`, `home-fragrance`.
The AI layer and filters use these exact values.

### Product
```
id                UUID pk
name_en, name_ar
slug              unique
sku               unique            # RAV-OUD-001
description_en, description_ar
category_fk
gender            enum: men | women | unisex
fragrance_family  enum (see below)
concentration     enum: parfum | edp | edt | edc | oil | bakhoor | home
longevity         enum: short | moderate | long | very_long
sillage           enum: intimate | moderate | strong | very_strong
intensity         enum: light | moderate | strong | very_strong
occasions         array of enum
seasons           array of enum
moods             array of enum
base_price        decimal(10,2)     # denormalised price of the default variant
is_featured, is_bestseller, is_new, is_active  bool
rating_avg        decimal(3,2) default 0
rating_count      int default 0
embedding         vector(768) null  # gemini-embedding-2, output_dimensionality=768
embedding_hash    varchar(64) null  # SHA-256 of the embedded text; skip re-embed if unchanged
created_at, updated_at
```
Indexes: `slug`, `sku`, `category_id`, `is_active`, `base_price`,
`(is_active, category_id)`, GIN on `occasions`, `seasons`, `moods`, and an **HNSW** index
on `embedding` with `vector_cosine_ops`. (IVFFlat needs existing rows to train its lists and
is pointless at 30 products; HNSW works on an empty table.)

**`base_price`** is the price of the *default variant* — the active variant with the
lowest `sort_order`. `ProductService` recomputes it whenever a variant's price, `is_active`
or `sort_order` changes. Never edit it directly. It is used for sorting and price filters
only; the price charged always comes from the chosen variant.

### ProductVariant
```
id UUID, product_fk, size_ml int, sku unique, price decimal(10,2),
compare_at_price decimal(10,2) null, stock int check >= 0,
is_active bool, sort_order
```
Unique: `(product_id, size_ml)`. A product must have at least one active variant.
`compare_at_price`, when set, must be greater than `price` (check constraint); that is
what marks a variant as on sale.

### ProductImage
```
id, product_fk, url, alt_en, alt_ar, sort_order, is_primary bool
```
Exactly one primary image per product — partial unique index on
`(product_id) WHERE is_primary`, maintained by the service.

### FragranceNote / ProductFragranceNote
```
FragranceNote:         id, name_en, name_ar, slug unique
ProductFragranceNote:  id, product_fk, note_fk, layer enum: top | heart | base, sort_order
```
Unique: `(product_id, note_id, layer)`.

### Cart / CartItem
```
Cart:      id UUID, user_fk null, session_key null, created_at, updated_at
CartItem:  id UUID, cart_fk, variant_fk, quantity int check > 0, added_at
```
A cart belongs to a user **or** a session, never neither (check constraint). Unique
`(cart_id, variant_id)`. On login, merge the session cart into the user cart, summing
quantities and clamping to stock. A cart does not reserve stock.

### Coupon / CouponUsage
```
Coupon:       id, code unique uppercase, type enum: percentage | fixed,
              value decimal, min_order_total decimal null, max_discount decimal null,
              starts_at, expires_at, usage_limit int null, used_count int default 0,
              is_active bool
CouponUsage:  id, coupon_fk, user_fk null, order_fk, used_at
```
Validate: active, within dates, under usage limit, order meets minimum.
Usage is consumed at order creation with a conditional update, never read-then-write:
```sql
UPDATE coupon SET used_count = used_count + 1
WHERE id = %s AND (usage_limit IS NULL OR used_count < usage_limit);
-- 0 rows updated → the coupon ran out; reject the order with a clear error
```
Cancelling an order before payment decrements `used_count` and deletes the usage row.

### Order
```
id                UUID pk
order_no          varchar(20) unique      # RAV-2026-00124, from a Postgres sequence
user_fk           null                    # null for guest checkout
email, full_name, phone
city, district, street, postal_code, delivery_notes
subtotal, discount, shipping, total       decimal(10,2)
vat_rate          decimal(5,2) default 15.00
vat_amount        decimal(10,2)
coupon_code       varchar(40) null        # snapshot, not a FK
payment_method    enum: mada | apple_pay | card | cod
status            enum: pending | confirmed | processing | shipped | delivered | cancelled
payment_status    enum: pending | paid | failed | refunded
payment_due_at    timestamptz null        # online methods: placed_at + PAYMENT_HOLD_MINUTES
placed_at, updated_at
```
Indexes: `order_no`, `user_id`, `status`, `placed_at`, `(status, payment_due_at)`.

### OrderItem — snapshots, so history never changes
```
id, order_fk,
product_name_en, product_name_ar, sku, size_ml,   # copied at purchase time
unit_price decimal(10,2), quantity int, line_total decimal(10,2),
variant_fk null on delete SET NULL                # used to return stock on cancellation
product_fk null on delete SET NULL                # link only, never the source of truth
```

### Payment
```
id, order_fk, provider varchar, provider_ref varchar null,
method enum: mada | apple_pay | card | cod,
amount decimal(10,2), status enum: pending | paid | failed | refunded,
raw_response jsonb, created_at, updated_at
```
Unique `(provider, provider_ref)` so a replayed webhook cannot be applied twice.

### Wishlist / WishlistItem
```
Wishlist:      id, user_fk unique
WishlistItem:  id UUID, wishlist_fk, product_fk, added_at   # unique (wishlist, product)
```

### Review
```
id, product_fk, user_fk, order_fk null, rating int check 1..5,
comment text, is_verified_purchase bool, is_approved bool default false, created_at
```
Unique `(product_id, user_id)`. `is_verified_purchase` is set by the server from the
user's delivered orders, never from input. Only approved reviews affect `rating_avg`.
Review text is untrusted: the AI layer treats it as data (see `docs/ai.md`).

### AIConversation / AIMessage
```
AIConversation: id UUID, user_fk null, session_key null, started_at, last_message_at
AIMessage:      id, conversation_fk, role enum: user | assistant | tool,
                content text, tool_name varchar null, tool_args jsonb null,
                tool_result jsonb null, tokens_in int, tokens_out int, created_at
```
Token counts are stored so daily spend can be measured and capped. Ownership rules apply:
a conversation is readable only by its user or session.

---

## Stock lifecycle

Stock is **taken at order creation** for every payment method, and **returned** when the
order is cancelled. Adding to cart reserves nothing.

Inside the order-creation transaction, per line:
```sql
UPDATE product_variant SET stock = stock - %(qty)s
WHERE id = %(variant_id)s AND is_active AND stock >= %(qty)s;
-- 0 rows updated → roll back the whole order: "Only N left in stock."
```
Never read stock, compare in Python, then write — two buyers would both get the last
unit. Lock variants in a consistent order (by id) to avoid deadlocks.

Stock is returned (`stock = stock + qty`) exactly once, when an order moves to
`cancelled` — by the customer, by staff, or by expiry.

## Order and payment lifecycle

**Online methods (mada, Apple Pay, card):**
```
order created      status=pending    payment_status=pending   stock taken, payment_due_at set
verify / webhook   status=confirmed  payment_status=paid
provider failure   status=pending    payment_status=failed    customer may retry until due
payment_due_at     status=cancelled  payment_status=failed    stock + coupon returned
passes unpaid
```
`release_expired_orders` (management command, scheduled every 10 minutes) cancels
pending orders past `payment_due_at`.

**Cash on delivery:**
```
order created      status=confirmed  payment_status=pending   stock taken, no due time
staff ships        status=shipped
staff marks        status=delivered  payment_status=paid      Payment row, provider="cod",
delivered + cash                                              recorded by the staff user
collected
refused at door    status=cancelled  payment_status=failed    stock returned
```
For COD the server-side confirmation that satisfies rule 5 is the authenticated staff
action. The customer can never set it.

**Refunds:** only from `paid`, via `PaymentService.refund_payment`, staff only.

---

## Order number sequence

Do not compute `MAX(order_no) + 1` — two simultaneous orders will collide.

Created in a migration with `RunSQL`:
```sql
CREATE SEQUENCE order_no_seq START 100;
-- RAV-2026-00124
SELECT 'RAV-' || date_part('year', now() AT TIME ZONE 'Asia/Riyadh')::int || '-' ||
       lpad(nextval('order_no_seq')::text, 5, '0');
```
The sequence is not reset yearly or by `seed_demo --reset`; numbers only ever increase.
Order numbers are guessable by design, so guest tracking never relies on them alone
(see `docs/api.md`).

---

## Enumerations

```
fragrance_family: woody oriental floral fresh citrus amber musk gourmand aquatic spicy leather oud
occasion:         daily office evening wedding date formal travel special
season:           spring summer autumn winter all_season
mood:             elegant fresh warm mysterious romantic confident calm energetic luxurious
```

Store these structurally. Never bury a searchable attribute inside the description text.

---

## Catalogue shape (30 products)

| Category (slug) | Count | Typical SAR |
|---|---|---|
| Perfumes (`perfumes`) | 10 | 220–650 |
| Oud (`oud`) | 5 | 380–1,200 |
| Attar (`attar`) | 4 | 120–420 |
| Bakhoor (`bakhoor`) | 4 | 90–280 |
| Gift Sets (`gift-sets`) | 4 | 350–1,400 |
| Home Fragrance (`home-fragrance`) | 3 | 150–450 |

Make the data uneven and therefore believable: 2 products on sale, 1 sold out, 3 new,
4 best sellers, a few with low stock.

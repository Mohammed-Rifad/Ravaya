# RAVAYA — رَفَايَا

**Crafted for Your Senses.**

An AI-powered fragrance e-commerce platform for the Saudi/GCC market. Fictional brand,
production-style engineering.

> Demo store. No real orders are processed and no real payments are taken.

## What it demonstrates

Full-stack development (Next.js + Django), a complete e-commerce workflow, PostgreSQL data
modelling with pgvector, LLM tool calling with strict guardrails, semantic search and
recommendations, secure authentication and authorization, payment abstraction, a custom
admin system, testing, and deployment.

## Stack

Next.js · React · TypeScript · Tailwind · Django · DRF · PostgreSQL · pgvector · Gemini

## Quick start

```bash
# backend
cd backend && python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env        # fill it in
python manage.py migrate
python manage.py seed_demo
python manage.py embed_products
python manage.py runserver

# frontend
cd frontend && npm install
cp ../.env.example .env.local  # only NEXT_PUBLIC_* values are used
npm run dev
```

## Documentation

- [`CLAUDE.md`](CLAUDE.md) — how this project is built (read first)
- [`docs/phases.md`](docs/phases.md) — the build plan
- [`docs/architecture.md`](docs/architecture.md)
- [`docs/database.md`](docs/database.md)
- [`docs/api.md`](docs/api.md)
- [`docs/ai.md`](docs/ai.md)
- [`docs/deployment.md`](docs/deployment.md)
- [`docs/decisions.md`](docs/decisions.md)

## Screenshots

_Add after Phase 3: home, shop, product, cart, checkout, AI consultant, admin dashboard._

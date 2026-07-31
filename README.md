# XMeme

[![CI](https://github.com/amulyavarshney/XMeme/actions/workflows/ci.yml/badge.svg)](https://github.com/amulyavarshney/XMeme/actions/workflows/ci.yml)
[![Pages](https://github.com/amulyavarshney/XMeme/actions/workflows/pages.yml/badge.svg)](https://github.com/amulyavarshney/XMeme/actions/workflows/pages.yml)
[![Live demo](https://img.shields.io/badge/demo-GitHub%20Pages-0f9f8a?logo=github)](https://amulyavarshney.github.io/XMeme/)

**Create, share, and discover memes** — canvas studio, auth, social feeds, and production-ready Docker deploy.

| Try it | URL |
|--------|-----|
| **Live UI** | [amulyavarshney.github.io/XMeme](https://amulyavarshney.github.io/XMeme/) |
| **Local API** | `http://localhost:8081` (pair with the live UI or local frontend) |
| **Health** | `GET /health` · `GET /ready` · `GET /live` |

> GitHub Pages hosts the **frontend only**. Point it at a local (or hosted) API — the UI shows an offline banner until `/health` responds.

---

## Contents

- [Quick start](#quick-start)
- [Pair Pages UI with local API](#pair-pages-ui-with-local-api)
- [Docker](#docker)
- [What you get](#what-you-get)
- [API snapshot](#api-snapshot)
- [Tests & CI](#tests--ci)
- [Production](#production)

---

## Quick start

<details open>
<summary><strong>1. Backend</strong> (terminal A)</summary>

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 app.py
```

API → [http://localhost:8081](http://localhost:8081) · docs → [http://localhost:8081/](http://localhost:8081/)

</details>

<details open>
<summary><strong>2. Frontend</strong> (terminal B)</summary>

```bash
cd frontend
python3 -m http.server 8001
```

UI → [http://localhost:8001](http://localhost:8001)

</details>

<details>
<summary><strong>One-liner with Docker (SQLite)</strong></summary>

```bash
docker compose -f docker-compose.dev.yml up --build
```

- UI: [http://localhost:8000](http://localhost:8000)
- API: [http://localhost:8081](http://localhost:8081)

</details>

---

## Pair Pages UI with local API

1. Start the backend (`python3 app.py` in `backend/`).
2. Open [the live demo](https://amulyavarshney.github.io/XMeme/).
3. Ensure CORS allows the Pages origin in `backend/.env`:

```env
CORS_ORIGINS=http://localhost:8000,http://localhost:8001,https://amulyavarshney.github.io
FRONTEND_URL=https://amulyavarshney.github.io/XMeme
```

The browser talks to `http://localhost:8081` from the Pages UI (see `frontend/config.js`).

---

## Docker

| Compose file | Use when |
|--------------|----------|
| `docker-compose.dev.yml` | Local SQLite + reload |
| `docker-compose.yml` | Postgres + Gunicorn + nginx `/api` proxy |

```bash
# Prod-like stack
cp .env.production.example .env   # set SECRET_KEY, etc.
docker compose up --build -d
```

---

## What you get

- **Studio** — multi-layer text, stickers, filters, crop, undo/redo, drafts, templates
- **Share** — per-meme pages, Open Graph tags, copy / social / download
- **Social** — likes, reactions, nested comments, follows, notifications, tags, trending
- **Ops** — JWT auth, rate limits, security headers, Alembic, health checks, CI + Pages deploy

---

## API snapshot

| Method | Path | Notes |
|--------|------|-------|
| `GET` | `/health` `/ready` `/live` | Probe endpoints |
| `POST` | `/auth/register` `/auth/login` | Rate limited |
| `GET` | `/memes` | Paginated feed |
| `POST` | `/upload` | Auth + magic-byte sniff |
| `GET` | `/admin/reports` | Set `ADMIN_USERNAMES` |

Full interactive docs when `ENABLE_DOCS=true` (default in development).

---

## Tests & CI

```bash
cd backend && pytest -q
```

- CI: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
- Pages: [`.github/workflows/pages.yml`](.github/workflows/pages.yml) → [live site](https://amulyavarshney.github.io/XMeme/)

---

## Production

1. Copy [`.env.production.example`](.env.production.example) → `.env`
2. Set a strong `SECRET_KEY` (`openssl rand -hex 32`)
3. Use Postgres, public HTTPS URLs, explicit `CORS_ORIGINS`
4. `docker compose up --build -d`

Checklist: HTTPS · volume backups · `ENABLE_DOCS=false` · monitor `/ready` · optional object storage for uploads.

### Migrations

```bash
cd backend
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```

Startup also runs `create_all` plus lightweight SQLite column patches for older local DBs.

---

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Vanilla HTML/CSS/JS (hash SPA), nginx, GitHub Pages |
| Backend | FastAPI, SQLAlchemy 2, Pydantic v2, Gunicorn |
| Auth | JWT Bearer |
| DB | SQLite (dev) / PostgreSQL (prod) |

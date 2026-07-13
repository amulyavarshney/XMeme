# XMeme

Create, share, and discover memes — canvas studio, auth, social, and production deploy tooling.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Vanilla HTML/CSS/JS (hash SPA) + nginx |
| Backend | FastAPI, SQLAlchemy 2, Pydantic v2, Gunicorn/Uvicorn |
| Auth | JWT Bearer |
| Database | SQLite (dev) / PostgreSQL (production) |
| Media | Local uploads volume (swap for object storage later) |

## Local development

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 app.py
```

```bash
cd frontend
python3 -m http.server 8001
```

- UI: http://localhost:8001
- API: http://localhost:8081
- Health: http://localhost:8081/health
- Ready: http://localhost:8081/ready

### Dev Docker (SQLite)

```bash
docker compose -f docker-compose.dev.yml up --build
```

## Production deploy

1. Copy `.env.production.example` → `.env` and set strong values:

```bash
openssl rand -hex 32   # SECRET_KEY
```

Required production settings:
- `SECRET_KEY` — 32+ character random secret (app refuses insecure defaults)
- `DATABASE_URL` — PostgreSQL (SQLite blocked in production)
- `API_PUBLIC_URL` / `FRONTEND_URL` — public HTTPS URLs (not localhost)
- `CORS_ORIGINS` — explicit origins (not `*`)
- `ADMIN_USERNAMES` — comma-separated usernames for `/admin/reports`

Local prod-like stack (Postgres + nginx proxy) defaults to `ENVIRONMENT=development` so localhost URLs work. For a real deploy, set `ENVIRONMENT=production` and public HTTPS URLs in `.env`.

2. Launch:

```bash
docker compose up --build -d
```

- Web: http://localhost:8000 (proxies `/api` → API)
- API: http://localhost:8081

Frontend `config.js` is generated at container start with `XMEME_API_BASE=/api` so the browser talks same-origin through nginx.

### Production checklist

- [ ] Strong `SECRET_KEY` and `POSTGRES_PASSWORD`
- [ ] HTTPS termination (Cloudflare / load balancer / Traefik)
- [ ] Persistent volumes for Postgres + uploads
- [ ] Backups for Postgres and uploads
- [ ] Set `ENABLE_DOCS=false` (default in compose)
- [ ] Monitor `/ready` and `/live`
- [ ] Optional: set `GIPHY_API_KEY` for stock search
- [ ] Replace local uploads with S3/GCS when scaling

## API highlights

| Method | Path | Notes |
|--------|------|-------|
| `GET` | `/health` | Liveness-ish status |
| `GET` | `/ready` | DB connectivity |
| `GET` | `/live` | Process alive |
| `POST` | `/auth/register` | Rate limited |
| `POST` | `/auth/login` | Rate limited |
| `POST` | `/upload` | Auth + magic-byte validation + rate limit |
| `GET` | `/memes` | Paginated feed |
| `GET` | `/admin/reports` | Moderation queue (auth required) |

## Tests / CI

```bash
cd backend
pytest -q
```

GitHub Actions runs the same suite on push/PR (`.github/workflows/ci.yml`).

## Migrations

Alembic is wired for forward migrations:

```bash
cd backend
alembic upgrade head
alembic revision --autogenerate -m "describe change"
```

Startup still runs `create_all` + lightweight SQLite column patches for older local DBs.

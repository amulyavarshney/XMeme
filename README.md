# XMeme

Create, share, and discover memes — with a canvas editor, auth, likes, comments, and trending.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Vanilla HTML/CSS/JS (hash SPA) |
| Backend | FastAPI, SQLAlchemy 2, Pydantic v2 |
| Auth | JWT (Bearer) |
| Database | SQLite (configurable via `DATABASE_URL`) |
| Media | Local uploads served at `/uploads` |

## Features

- **Foundation** — pagination, timestamps, delete, Docker Compose, upgraded deps
- **Create** — image upload + canvas meme editor (text overlays, templates)
- **Share** — per-meme pages, OG meta (`/share/{id}`), copy-link / X / Reddit
- **Social** — register/login, likes, comments, profiles, trending

## Quick start

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional
python3 app.py
```

- API + Swagger: http://localhost:8081/
- ReDoc: http://localhost:8081/doc
- Health: http://localhost:8081/health

### Frontend

```bash
cd frontend
python3 -m http.server 8000
```

Open http://localhost:8000

Override the API base if needed:

```html
<script>window.XMEME_API_BASE = "http://localhost:8081";</script>
```

## Docker Compose

```bash
docker compose up --build
```

- Web: http://localhost:8000
- API: http://localhost:8081

## API overview

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/register` | — | Create account |
| `POST` | `/auth/login` | — | OAuth2 password → JWT |
| `GET` | `/auth/me` | ✓ | Current user |
| `GET` | `/memes?page=&page_size=` | optional | Paginated feed |
| `GET` | `/memes/trending` | optional | Trending by likes/views |
| `POST` | `/memes` | optional | Create meme |
| `GET` | `/memes/{id}` | optional | Meme detail (`track_view=true`) |
| `PATCH` | `/memes/{id}` | ✓ | Update (owner) |
| `DELETE` | `/memes/{id}` | ✓ | Delete (owner) |
| `POST` | `/memes/{id}/like` | ✓ | Toggle like |
| `GET/POST` | `/memes/{id}/comments` | POST ✓ | Comments |
| `POST` | `/upload` | ✓ | Upload image |
| `GET` | `/templates` | — | Editor templates |
| `GET` | `/users/{username}` | — | Profile |
| `GET` | `/share/{id}` | — | HTML + Open Graph tags |

## Project layout

```
XMeme/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── uploads/
│   └── src/
│       ├── main.py
│       ├── config.py
│       ├── models.py
│       ├── schemas.py
│       ├── auth.py
│       ├── crud.py
│       └── routers/
└── frontend/
    ├── index.html
    ├── app.js
    ├── api.js
    ├── editor.js
    ├── config.js
    └── style.css
```

## Environment

See `backend/.env.example`:

- `SECRET_KEY` — JWT signing key
- `DATABASE_URL` — SQLAlchemy URL
- `API_PUBLIC_URL` — public API origin (upload URLs + OG)
- `FRONTEND_URL` — used in share redirects
- `CORS_ORIGINS` — `*` or comma-separated list

# XMeme Backend

FastAPI service powering auth, memes, uploads, social features, and OG share pages.

## Run

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Listens on `0.0.0.0:8081`.

## Modules

- `src/main.py` — app, CORS, static uploads, routers
- `src/auth.py` — JWT + password hashing
- `src/routers/` — auth, memes, upload, users, share
- `src/migrate.py` — additive SQLite column migrations
- `src/seed.py` — default meme templates

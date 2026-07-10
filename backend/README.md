# XMeme Backend

FastAPI service for creating, listing, and updating memes.

## Features

- REST API for memes (`POST`, `GET`, `PATCH`)
- SQLAlchemy + SQLite persistence
- CORS enabled for local frontend development
- Swagger UI at `/` and ReDoc at `/doc`

## Local run

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 app.py
```

Server listens on `http://0.0.0.0:8081`.

## Endpoints

| Method | Path | Notes |
|--------|------|-------|
| `POST` | `/memes` | Body: `{ "name", "url", "caption" }` → `{ "id" }` |
| `GET` | `/memes` | Returns all memes |
| `GET` | `/memes/{id}` | Single meme or `404` |
| `PATCH` | `/memes/{id}` | Partial update of `url` / `caption` |

## Structure

```
backend/
├── app.py              # Uvicorn entrypoint
├── requirements.txt
├── xmeme.db            # SQLite database
└── src/
    ├── main.py         # FastAPI routes
    ├── models.py       # SQLAlchemy models
    ├── schemas.py      # Pydantic schemas
    ├── crud.py         # Database helpers
    └── database.py     # Engine & session
```

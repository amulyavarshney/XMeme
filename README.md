# XMeme

A meme stream platform for posting, browsing, and editing memes.

Drop an image URL, add a caption, and share it with the feed. Built with a FastAPI backend and a lightweight vanilla frontend.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, FastAPI, SQLAlchemy |
| Database | SQLite (`backend/xmeme.db`) |

## Quick start

### Backend

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 app.py
```

- API: http://localhost:8081
- Swagger UI: http://localhost:8081/
- ReDoc: http://localhost:8081/doc

### Frontend

Serve the `frontend` folder (opening `index.html` via `file://` may block API calls):

```bash
cd frontend
python3 -m http.server 8000
```

Open http://localhost:8000 — the UI expects the API on port `8081`.

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/memes` | Create a meme (`name`, `url`, `caption`) |
| `GET` | `/memes` | List all memes |
| `GET` | `/memes/{id}` | Get one meme |
| `PATCH` | `/memes/{id}` | Update `url` and/or `caption` |

Duplicate posts (same name + url + caption) return `409`.

## Docker

### Backend

```bash
cd backend
docker build -t xmeme-api:v1 .
docker run -d --name xmeme-api -p 8081:8081 xmeme-api:v1
```

### Frontend

```bash
cd frontend
docker build -t xmeme-web:v1 .
docker run -d --name xmeme-web -p 80:80 xmeme-web:v1
```

## Project layout

```
XMeme/
├── backend/          # FastAPI app
│   ├── app.py        # Dev server entry
│   ├── src/          # Routes, models, CRUD
│   └── requirements.txt
└── frontend/         # Static UI
    ├── index.html
    ├── app.js
    ├── style.css
    └── images/
```

## License

Personal project — use and extend as you like.

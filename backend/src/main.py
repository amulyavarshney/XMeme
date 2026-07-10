from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import Base, engine
from .migrate import migrate
from .seed import seed_templates
from .routers import auth, discover, memes, share, upload, users

settings = get_settings()

Base.metadata.create_all(bind=engine)
migrate()
seed_templates()

app = FastAPI(
    title=settings.app_name,
    description="Create, share, and discover memes.",
    version="2.1.0",
    docs_url="/",
    redoc_url="/doc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(settings.upload_path)), name="uploads")

app.include_router(auth.router)
app.include_router(memes.router)
app.include_router(upload.router)
app.include_router(users.router)
app.include_router(discover.router)
app.include_router(share.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}

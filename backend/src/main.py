from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text

from .config import get_settings
from .database import Base, SessionLocal, engine
from .logging_config import configure_logging
from .middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from .migrate import migrate
from .rate_limit import limiter
from .routers import auth, discover, memes, share, upload, users
from .seed import seed_templates

settings = get_settings()
configure_logging(settings.log_level)

Base.metadata.create_all(bind=engine)
migrate()
if settings.seed_on_startup:
    seed_templates()

app = FastAPI(
    title=settings.app_name,
    description="Create, share, and discover memes.",
    version="2.2.0",
    docs_url="/" if settings.docs_enabled else None,
    redoc_url="/doc" if settings.docs_enabled else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestContextMiddleware)

if settings.trusted_host_list != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_host_list)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=settings.cors_origin_list != ["*"],
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
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
        "version": "2.2.0",
    }


@app.get("/ready")
def ready():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "error", "detail": str(exc)},
        )


@app.get("/live")
def live():
    return {"status": "alive"}

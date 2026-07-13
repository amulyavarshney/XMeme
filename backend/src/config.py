from functools import lru_cache
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_SECRETS = {
    "",
    "change-me",
    "change-me-in-production",
    "xmeme-dev-secret-change-me-in-production",
    "secret",
    "password",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "XMeme"
    environment: str = "development"
    secret_key: str = "xmeme-dev-secret-change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    database_url: str = "sqlite:///./xmeme.db"
    upload_dir: str = "uploads"
    api_public_url: str = "http://localhost:8081"
    frontend_url: str = "http://localhost:8001"
    cors_origins: str = "http://localhost:8000,http://localhost:8001"
    default_page_size: int = 12
    max_page_size: int = 50
    max_upload_bytes: int = 8 * 1024 * 1024
    giphy_api_key: str = ""
    rate_limit: str = "120/minute"
    auth_rate_limit: str = "10/minute"
    upload_rate_limit: str = "20/minute"
    seed_on_startup: bool = True
    enable_docs: bool | None = None
    trusted_hosts: str = "*"
    log_level: str = "INFO"
    admin_usernames: str = ""

    @property
    def admin_username_set(self) -> set[str]:
        return {u.strip().lower() for u in self.admin_usernames.split(",") if u.strip()}

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"prod", "production"}

    @property
    def docs_enabled(self) -> bool:
        if self.enable_docs is None:
            return not self.is_production
        return self.enable_docs

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        if self.trusted_hosts.strip() == "*":
            return ["*"]
        return [h.strip() for h in self.trusted_hosts.split(",") if h.strip()]

    @field_validator("environment")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def validate_production(self):
        if not self.is_production:
            return self
        if self.secret_key.strip() in INSECURE_SECRETS or len(self.secret_key) < 32:
            raise ValueError(
                "SECRET_KEY must be a strong unique value (32+ chars) in production"
            )
        if self.database_url.startswith("sqlite"):
            raise ValueError("DATABASE_URL must use PostgreSQL in production")
        if self.cors_origins.strip() == "*":
            raise ValueError("CORS_ORIGINS cannot be '*' in production")
        if "localhost" in self.api_public_url or "localhost" in self.frontend_url:
            raise ValueError("API_PUBLIC_URL and FRONTEND_URL must be public URLs in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

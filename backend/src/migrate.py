"""Lightweight SQLite migrations for additive schema changes."""

from sqlalchemy import inspect, text

from .database import engine

MEME_COLUMNS = {
    "user_id": "INTEGER",
    "created_at": "DATETIME",
    "updated_at": "DATETIME",
    "view_count": "INTEGER DEFAULT 0",
    "share_count": "INTEGER DEFAULT 0",
    "download_count": "INTEGER DEFAULT 0",
    "status": "VARCHAR(20) DEFAULT 'published'",
    "visibility": "VARCHAR(20) DEFAULT 'public'",
    "editor_state": "TEXT DEFAULT ''",
    "media_type": "VARCHAR(20) DEFAULT 'image'",
    "tags_raw": "VARCHAR(255) DEFAULT ''",
}

USER_COLUMNS = {
    "is_private": "BOOLEAN DEFAULT 0",
    "onboarding_done": "BOOLEAN DEFAULT 0",
}

TEMPLATE_COLUMNS = {
    "category": "VARCHAR(50) DEFAULT 'blank'",
    "user_id": "INTEGER",
    "is_public": "BOOLEAN DEFAULT 1",
    "created_at": "DATETIME",
}

COMMENT_COLUMNS = {
    "parent_id": "INTEGER",
}


def _has_table(table: str) -> bool:
    return table in inspect(engine).get_table_names()


def _has_column(table: str, column: str) -> bool:
    insp = inspect(engine)
    if table not in insp.get_table_names():
        return False
    return any(col["name"] == column for col in insp.get_columns(table))


def _add_missing(table: str, columns: dict):
    with engine.begin() as conn:
        for name, ddl in columns.items():
            if not _has_column(table, name):
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def migrate():
    if _has_table("memes"):
        _add_missing("memes", MEME_COLUMNS)
        with engine.begin() as conn:
            conn.execute(text("UPDATE memes SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
            conn.execute(text("UPDATE memes SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"))
            conn.execute(text("UPDATE memes SET view_count = 0 WHERE view_count IS NULL"))
            conn.execute(text("UPDATE memes SET share_count = 0 WHERE share_count IS NULL"))
            conn.execute(text("UPDATE memes SET download_count = 0 WHERE download_count IS NULL"))
            conn.execute(text("UPDATE memes SET status = 'published' WHERE status IS NULL OR status = ''"))
            conn.execute(text("UPDATE memes SET visibility = 'public' WHERE visibility IS NULL OR visibility = ''"))
            conn.execute(text("UPDATE memes SET media_type = 'image' WHERE media_type IS NULL OR media_type = ''"))
    if _has_table("users"):
        _add_missing("users", USER_COLUMNS)
    if _has_table("templates"):
        _add_missing("templates", TEMPLATE_COLUMNS)
        # Drop unique name constraint isn't easy on SQLite; allow duplicate names via app logic for user templates
    if _has_table("comments"):
        _add_missing("comments", COMMENT_COLUMNS)

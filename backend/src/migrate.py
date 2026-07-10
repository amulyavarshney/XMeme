"""Lightweight SQLite migrations for additive schema changes."""

from sqlalchemy import inspect, text

from .database import engine


def _has_column(table: str, column: str) -> bool:
    insp = inspect(engine)
    if table not in insp.get_table_names():
        return False
    return any(col["name"] == column for col in insp.get_columns(table))


def migrate():
    with engine.begin() as conn:
        if _has_table("memes"):
            alters = []
            if not _has_column("memes", "user_id"):
                alters.append("ALTER TABLE memes ADD COLUMN user_id INTEGER")
            if not _has_column("memes", "created_at"):
                alters.append("ALTER TABLE memes ADD COLUMN created_at DATETIME")
            if not _has_column("memes", "updated_at"):
                alters.append("ALTER TABLE memes ADD COLUMN updated_at DATETIME")
            if not _has_column("memes", "view_count"):
                alters.append("ALTER TABLE memes ADD COLUMN view_count INTEGER DEFAULT 0")
            for stmt in alters:
                conn.execute(text(stmt))
            conn.execute(
                text(
                    "UPDATE memes SET created_at = CURRENT_TIMESTAMP "
                    "WHERE created_at IS NULL"
                )
            )
            conn.execute(
                text(
                    "UPDATE memes SET updated_at = CURRENT_TIMESTAMP "
                    "WHERE updated_at IS NULL"
                )
            )
            conn.execute(
                text("UPDATE memes SET view_count = 0 WHERE view_count IS NULL")
            )


def _has_table(table: str) -> bool:
    return table in inspect(engine).get_table_names()

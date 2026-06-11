from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from server.app.config import ROOT, get_settings

MIGRATIONS_DIR = ROOT / "server" / "migrations"


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True, future=True)


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)


@contextmanager
def db_session() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db_session() -> Iterator[Session]:
    with db_session() as session:
        yield session


def check_database_connection() -> None:
    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))


def migration_files(migrations_dir: Path = MIGRATIONS_DIR) -> list[Path]:
    if not migrations_dir.exists():
        return []
    return sorted(path for path in migrations_dir.glob("*.sql") if path.is_file())


def apply_migrations(migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    applied: list[str] = []
    with get_engine().begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                  version text PRIMARY KEY,
                  applied_at timestamptz NOT NULL DEFAULT now()
                )
                """
            )
        )
        seen = {
            row[0]
            for row in connection.execute(text("SELECT version FROM schema_migrations")).all()
        }
        for path in migration_files(migrations_dir):
            version = path.name
            if version in seen:
                continue
            sql = path.read_text(encoding="utf-8")
            connection.exec_driver_sql(sql)
            connection.execute(text("INSERT INTO schema_migrations (version) VALUES (:version)"), {"version": version})
            applied.append(version)
    return applied

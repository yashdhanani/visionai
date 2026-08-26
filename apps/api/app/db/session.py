from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.settings import settings


class Base(DeclarativeBase):
    pass


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        return {
            "connect_args": {"check_same_thread": False, "timeout": 30},
            "pool_pre_ping": True,
        }
    return {"pool_size": 10, "max_overflow": 20, "pool_pre_ping": True}


import urllib.parse

def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://") or url.startswith("postgresql://"):
        scheme = "postgresql"
        rest = url.split("://", 1)[1]
        if "@" in rest:
            auth, host_path = rest.rsplit("@", 1)
            if ":" in auth:
                user, raw_password = auth.split(":", 1)
                unquoted_pass = urllib.parse.unquote(raw_password)
                encoded_password = urllib.parse.quote(unquoted_pass, safe="")
                return f"{scheme}://{user}:{encoded_password}@{host_path}"
        return f"{scheme}://{rest}"
    return url


db_url = _normalize_database_url(settings.DATABASE_URL)

if db_url.startswith("sqlite") and ":memory:" not in db_url:
    os.makedirs(os.path.dirname(db_url.replace("sqlite:///", "")) or ".", exist_ok=True)

engine = create_engine(db_url, **_engine_kwargs(db_url))

if db_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def db_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

import logging
import os
import urllib.parse
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.settings import settings

logger = logging.getLogger("visionai.db")


class Base(DeclarativeBase):
    pass


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        return {
            "connect_args": {"check_same_thread": False, "timeout": 30},
            "pool_pre_ping": True,
        }
    return {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,
        "connect_args": {"connect_timeout": 5},
    }


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


def _init_engine():
    raw_url = settings.DATABASE_URL
    db_url = _normalize_database_url(raw_url)

    if db_url.startswith("postgresql"):
        try:
            eng = create_engine(db_url, **_engine_kwargs(db_url))
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to PostgreSQL database")
            return eng, db_url
        except Exception as err:
            logger.warning(
                f"Failed to connect to PostgreSQL ({err}). Falling back to local SQLite database."
            )
            fallback_dir = os.path.join(os.getcwd(), "data")
            os.makedirs(fallback_dir, exist_ok=True)
            fallback_url = f"sqlite:///{os.path.join(fallback_dir, 'visionai.db')}"
            eng = create_engine(fallback_url, **_engine_kwargs(fallback_url))
            return eng, fallback_url
    else:
        if db_url.startswith("sqlite") and ":memory:" not in db_url:
            path = db_url.replace("sqlite:///", "")
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        eng = create_engine(db_url, **_engine_kwargs(db_url))
        return eng, db_url


engine, db_url = _init_engine()

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

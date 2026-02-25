import os
from urllib.parse import urlparse, quote_plus

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

Base = declarative_base()

_engine = None
_is_sqlite = False


def get_engine():
    global _engine, _is_sqlite
    if _engine is not None:
        return _engine

    raw = os.environ.get("DATABASE_URL", "")

    if raw and not raw.startswith("sqlite"):
        p = urlparse(raw)
        user = quote_plus(p.username or "")
        pwd = quote_plus(p.password or "")
        host = p.hostname
        port = p.port or 5432
        db = p.path or ""

        url = f"postgresql://{user}:{pwd}@{host}:{port}{db}"

        _engine = create_engine(
            url,
            connect_args={"sslmode": "require"},
            poolclass=NullPool,
        )
    else:
        _is_sqlite = True
        # /tmp is writable on Vercel serverless; fall back to project root locally
        tmp = "/tmp" if os.path.isdir("/tmp") else os.path.join(
            os.path.dirname(os.path.abspath(__file__)), ".."
        )
        db_path = os.path.join(tmp, "local.db")
        url = f"sqlite:///{os.path.abspath(db_path)}"
        _engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return _engine


def get_db():
    Session = sessionmaker(bind=get_engine())
    db = Session()
    try:
        yield db
    finally:
        db.close()

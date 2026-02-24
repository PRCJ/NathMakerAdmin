import os
from urllib.parse import urlparse, quote_plus

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

Base = declarative_base()

_engine = None


def get_engine():
    global _engine
    if _engine is not None:
        return _engine

    raw = os.environ.get("DATABASE_URL", "")

    if not raw or raw.startswith("sqlite"):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "local.db")
        url = f"sqlite:///{os.path.abspath(db_path)}"
        _engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        # Enable FK support for SQLite
        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    else:
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

    return _engine


def get_db():
    Session = sessionmaker(bind=get_engine())
    db = Session()
    try:
        yield db
    finally:
        db.close()

import os
import ssl
from urllib.parse import urlparse, quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

Base = declarative_base()

# Lazy engine — only created on first DB request, not at import time
_engine = None


def get_engine():
    global _engine
    if _engine is not None:
        return _engine

    raw = os.environ.get("DATABASE_URL", "")
    if not raw:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    p = urlparse(raw)

    # URL-encode credentials to handle special characters
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

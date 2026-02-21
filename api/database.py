import os
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool


def get_clean_database_url() -> str:
    """
    Read DATABASE_URL and strip parameters psycopg2 doesn't support
    (e.g. channel_binding=require which is Neon-specific).
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    # Remove params unsupported by psycopg2
    params.pop("channel_binding", None)

    new_query = urlencode({k: v[0] for k, v in params.items()})
    clean = urlunparse(parsed._replace(query=new_query))
    return clean


DATABASE_URL = get_clean_database_url()

# NullPool is the right choice for serverless — no persistent connections
engine = create_engine(DATABASE_URL, poolclass=NullPool)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

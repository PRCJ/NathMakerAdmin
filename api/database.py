import os
import ssl
from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool


def _build_engine():
    raw_url = os.environ.get("DATABASE_URL")
    if not raw_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    # Parse original URL to extract components
    p = urlparse(raw_url)

    # Rebuild as pg8000 dialect URL (pure Python, works on Vercel Lambda)
    pg8000_url = (
        f"postgresql+pg8000://{p.username}:{p.password}"
        f"@{p.hostname}:{p.port or 5432}{p.path}"
    )

    # SSL context required for Neon
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED
    ssl_ctx.check_hostname = True

    return create_engine(
        pg8000_url,
        connect_args={"ssl_context": ssl_ctx},
        poolclass=NullPool,   # Required for serverless — no persistent connections
    )


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

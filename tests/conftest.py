import os

os.environ["TESTING"] = "1"
os.environ["ADMIN_PASSWORD"] = "test-admin-password"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.pop("VERCEL_ENV", None)
os.environ.pop("ENABLE_DOCS", None)
os.environ.pop("ALLOW_ALL_ORIGINS", None)

import pytest
from fastapi.testclient import TestClient

from api.index import app, _login_failures
from core.database import Base, get_engine

TEST_ADMIN_PASSWORD = "test-admin-password"


@pytest.fixture
def client():
    _login_failures.clear()
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_client(client):
    response = client.post(
        "/admin/login",
        data={"password": TEST_ADMIN_PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code == 302
    return client

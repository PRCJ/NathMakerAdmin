from tests.conftest import TEST_ADMIN_PASSWORD


def test_health_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_catalogues_public(client):
    response = client.get("/api/catalogues")
    assert response.status_code == 200
    assert response.json() == []


def test_get_products_public(client):
    response = client.get("/api/products")
    assert response.status_code == 200
    assert response.json() == []


def test_post_catalogue_requires_auth(client):
    response = client.post("/api/catalogues", json={"name": "Bridal"})
    assert response.status_code == 401


def test_post_product_requires_auth(client):
    response = client.post(
        "/api/products",
        json={"catalogueId": 1, "productName": "Nath", "price": 100},
    )
    assert response.status_code == 401


def test_put_product_requires_auth(client):
    response = client.put(
        "/api/products/1",
        json={"catalogueId": 1, "productName": "Nath", "price": 100},
    )
    assert response.status_code == 401


def test_delete_product_requires_auth(client):
    response = client.delete("/api/products/1")
    assert response.status_code == 401


def test_upload_requires_auth(client):
    response = client.post(
        "/api/upload",
        files={"file": ("x.png", b"not-an-image", "image/png")},
    )
    assert response.status_code == 401


def test_upload_status_reports_blob_unconfigured(client):
    response = client.get("/api/upload-status")
    assert response.status_code == 200
    body = response.json()
    assert body["storage"] == "vercel_blob"
    assert body["configured"] is False
    assert body["gemini_configured"] is False
    assert "watermark_logo" in body
    assert body["photo_pipeline"] == "gemini-or-studio"


def test_normalize_image_types():
    from core.blob_store import normalize_image_type

    assert normalize_image_type("image/jpg", "a.jpg") == "image/jpeg"
    assert normalize_image_type("application/octet-stream", "ring.png") == "image/png"
    assert normalize_image_type("image/png", "x") == "image/png"
    assert normalize_image_type("image/jfif", "images (12).jfif") == "image/jpeg"
    assert normalize_image_type("application/octet-stream", "shot.jfif") == "image/jpeg"


def test_upload_without_blob_config(auth_client):
    response = auth_client.post(
        "/api/upload",
        files={"file": ("x.png", b"xxxx", "image/png")},
    )
    assert response.status_code == 500
    assert "Vercel Blob is not configured" in response.json()["detail"]


def test_reset_db_removed(client):
    response = client.get("/admin/reset-db")
    assert response.status_code == 404
    assert "Database reset" not in response.text


def test_init_db_removed(client):
    response = client.get("/admin/init-db")
    assert response.status_code == 404
    assert "tables created" not in response.text


def test_excel_parse_requires_auth(client):
    response = client.post(
        "/api/products/excel-parse",
        files={"file": ("p.csv", b"productName,price\nA,1\n", "text/csv")},
    )
    assert response.status_code == 401


def test_excel_parse_with_auth(auth_client):
    response = auth_client.post(
        "/api/products/excel-parse",
        files={"file": ("p.csv", b"image\nhttps://x.test/a.jpg\n", "text/csv")},
    )
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert rows[0]["productName"] == "a"
    assert rows[0]["imageRefs"] == ["https://x.test/a.jpg"]


def test_bulk_page_requires_login(client):
    response = client.get("/admin/products/bulk", follow_redirects=False)
    assert response.status_code == 302
    assert "/admin/login" in response.headers.get("location", "")


def test_docs_disabled(client):
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_login_wrong_password(client):
    response = client.post(
        "/admin/login",
        data={"password": "wrong"},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "Invalid password" in response.text


def test_login_then_create_catalogue(auth_client):
    response = auth_client.post("/api/catalogues", json={"name": "Bridal"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Bridal"
    assert body["id"] >= 1


def test_login_then_create_and_read_product(auth_client):
    cat = auth_client.post("/api/catalogues", json={"name": "Bridal"}).json()
    created = auth_client.post(
        "/api/products",
        json={
            "catalogueId": cat["id"],
            "productName": "Gold Nath",
            "price": 2500,
        },
    )
    assert created.status_code == 201
    product_id = created.json()["id"]

    listed = auth_client.get("/api/products")
    assert listed.status_code == 200
    assert listed.json()[0]["productName"] == "Gold Nath"

    detail = auth_client.get(f"/api/products/{product_id}")
    assert detail.status_code == 200
    assert detail.json()["price"] == 2500


def test_login_rate_limited(client):
    for _ in range(5):
        response = client.post(
            "/admin/login",
            data={"password": "wrong"},
            follow_redirects=False,
        )
        assert response.status_code == 200

    blocked = client.post(
        "/admin/login",
        data={"password": TEST_ADMIN_PASSWORD},
        follow_redirects=False,
    )
    assert blocked.status_code == 429
    assert "Too many attempts" in blocked.text

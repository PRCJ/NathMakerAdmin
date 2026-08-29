import io

from PIL import Image

def _jpeg_bytes(width=800, height=800, color=(240, 230, 210)):
    image = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()


def test_logo_is_bundled_next_to_watermark_module():
    from core.watermark import logo_path

    path = logo_path()
    assert path
    assert path.endswith("logo.png")


def test_upload_status_reports_gemini_and_watermark(client):
    body = client.get("/api/upload-status").json()
    assert body["gemini_configured"] is False
    assert body["watermark_logo"] is True
    assert body["photo_pipeline"] == "studio-then-ai"
    assert "gemini_quota" in body
    assert body["horde_enabled"] is False


def test_enhance_requires_auth(client):
    response = client.post("/api/images/enhance", json={"imageUrl": "https://x.test/a.jpg"})
    assert response.status_code == 401


def test_enhance_without_gemini_key(auth_client):
    response = auth_client.post(
        "/api/images/enhance",
        json={"imageUrl": "https://x.test/a.jpg", "enhance": True},
    )
    assert response.status_code == 503
    assert "GEMINI_API_KEY" in response.json()["detail"]


def test_enhance_rejects_non_http_url(auth_client):
    response = auth_client.post(
        "/api/images/enhance",
        json={"imageUrl": "not-a-url", "enhance": False, "watermark": True},
    )
    assert response.status_code == 400


def test_review_watermark_flags_tiny_and_huge_marks():
    from core.watermark import review_watermark

    base = Image.new("RGB", (1000, 1000), (240, 230, 210))
    tiny = review_watermark(base, Image.new("RGBA", (20, 20), (0, 0, 0, 255)))
    huge = review_watermark(base, Image.new("RGBA", (400, 400), (0, 0, 0, 255)))
    good = review_watermark(base, Image.new("RGBA", (120, 40), (0, 0, 0, 255)))
    assert tiny["ok"] is False
    assert huge["ok"] is False
    assert good["ok"] is True


def test_apply_logo_watermark_reviews_size():
    from core.watermark import apply_logo_watermark

    out, review = apply_logo_watermark(_jpeg_bytes())
    assert out[:2] == b"\xff\xd8"
    assert review["ok"] is True
    assert 0.06 <= review["width_ratio"] <= 0.22
    assert any("balanced" in note for note in review["notes"])


def test_studio_remake_is_never_the_original():
    import io

    from core.studio_remake import studio_remake

    original = _jpeg_bytes(640, 400, (30, 30, 30))
    remade = studio_remake(original)
    assert remade != original
    assert remade[:2] == b"\xff\xd8"
    image = Image.open(io.BytesIO(remade))
    assert image.width == image.height


def test_prepare_photo_never_keeps_raw_bytes():
    from core.image_pipeline import prepare_product_photo

    original = _jpeg_bytes(640, 480, (20, 20, 20))
    prepared = prepare_product_photo(original, "image/jpeg", enhance=True, watermark=False)
    assert prepared["enhanced"] is False
    assert prepared["data"] != original
    assert prepared["data"][:2] == b"\xff\xd8"
    assert any("studio remake" in note.lower() for note in prepared["notes"])


def test_prepare_photo_skips_gemini_after_quota(monkeypatch):
    from core import gemini_enhance
    from core.image_pipeline import prepare_product_photo

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    gemini_enhance.reset_quota_cooldown()
    gemini_enhance.mark_quota_cooldown(120, "test 429")
    try:
        prepared = prepare_product_photo(_jpeg_bytes(), "image/jpeg", enhance=True, watermark=True)
    finally:
        gemini_enhance.reset_quota_cooldown()
    assert prepared["enhanced"] is False
    assert prepared["watermark"]["ok"] is True
    assert prepared["data"][:2] == b"\xff\xd8"
    assert any("studio remake" in note.lower() or "horde" in note.lower() or "quota" in note.lower() for note in prepared["notes"])


def test_retry_after_billing_quota_is_long():
    from core.gemini_enhance import _retry_after_seconds

    class Fake:
        headers = {}
        text = 'You exceeded your current quota, please check your plan and billing details.'

    assert _retry_after_seconds(Fake()) >= 3600


def test_resolve_photo_flags_default_to_fixing():
    from core.image_pipeline import resolve_photo_flags

    enhance, watermark = resolve_photo_flags(None, None)
    assert enhance is True
    assert watermark is True
    assert resolve_photo_flags(False, False) == (False, False)


def test_prepare_photo_watermarks_without_gemini():
    from core.image_pipeline import prepare_product_photo

    prepared = prepare_product_photo(_jpeg_bytes(), "image/jpeg", enhance=False, watermark=True)
    assert prepared["enhanced"] is False
    assert prepared["watermark"]["ok"] is True
    assert prepared["data"][:2] == b"\xff\xd8"

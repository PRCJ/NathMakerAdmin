import io

from PIL import Image

from core.blob_store import MAX_IMAGE_BYTES
from core.gemini_enhance import enhance_jewellery_photo, gemini_configured
from core.watermark import apply_logo_watermark


def jpeg_under_limit(image_bytes: bytes, max_bytes: int = MAX_IMAGE_BYTES) -> bytes:
    if len(image_bytes) <= max_bytes:
        return image_bytes
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    longest = max(image.size)
    if longest > 1600:
        scale = 1600 / longest
        image = image.resize(
            (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
            Image.Resampling.LANCZOS,
        )
    for quality in (88, 80, 72, 64):
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=quality, optimize=True)
        if buf.tell() <= max_bytes:
            return buf.getvalue()
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=55, optimize=True)
    return buf.getvalue()


def resolve_photo_flags(enhance, watermark):
    if enhance is None:
        enhance = gemini_configured()
    if watermark is None:
        watermark = True
    return bool(enhance), bool(watermark)


def prepare_product_photo(data: bytes, mime: str, enhance: bool, watermark: bool):
    notes = []
    enhanced = False
    review = None
    out_mime = mime or "image/jpeg"

    if enhance:
        if not gemini_configured():
            raise RuntimeError("GEMINI_API_KEY is not set in Vercel.")
        data = enhance_jewellery_photo(data, out_mime)
        out_mime = "image/jpeg"
        enhanced = True
        notes.append("Gemini applied a studio catalogue look.")

    if watermark:
        data, review = apply_logo_watermark(data, out_mime)
        out_mime = "image/jpeg"

    if out_mime == "image/jpeg" or enhanced or watermark:
        data = jpeg_under_limit(data)
        out_mime = "image/jpeg"

    return {
        "data": data,
        "mime": out_mime,
        "enhanced": enhanced,
        "watermark": review,
        "notes": notes,
    }

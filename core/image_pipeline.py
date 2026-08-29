import io

from PIL import Image, ImageEnhance, ImageOps

from core.blob_store import MAX_IMAGE_BYTES

from core.gemini_enhance import (
    GeminiQuotaExceeded,
    enhance_jewellery_photo,
    gemini_configured,
    quota_blocked,
    quota_status,
)
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


def local_studio_polish(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = ImageOps.exif_transpose(image)
    image = ImageEnhance.Contrast(image).enhance(1.12)
    image = ImageEnhance.Color(image).enhance(1.06)
    image = ImageEnhance.Sharpness(image).enhance(1.18)
    side = max(image.size)
    canvas = Image.new("RGB", (side, side), (245, 240, 232))
    canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def prepare_product_photo(data: bytes, mime: str, enhance: bool, watermark: bool):
    notes = []
    enhanced = False
    review = None
    out_mime = mime or "image/jpeg"

    if enhance:
        if not gemini_configured():
            notes.append("GEMINI_API_KEY is not set; applied a local studio crop instead.")
            data = local_studio_polish(data)
            out_mime = "image/jpeg"
        elif quota_blocked():
            wait = quota_status()["retry_after_seconds"]
            notes.append(
                f"Gemini quota is cooling down ({wait}s). Saved a local studio crop instead."
            )
            data = local_studio_polish(data)
            out_mime = "image/jpeg"
        else:
            try:
                data = enhance_jewellery_photo(data, out_mime)
                out_mime = "image/jpeg"
                enhanced = True
                notes.append("Gemini applied a studio catalogue look.")
            except GeminiQuotaExceeded as exc:
                notes.append(str(exc) + " Applied a local studio crop so the product still uploads.")
                data = local_studio_polish(data)
                out_mime = "image/jpeg"
            except Exception as exc:
                notes.append(
                    "Gemini could not enhance this photo; applied a local studio crop. "
                    + str(exc)[:160]
                )
                data = local_studio_polish(data)
                out_mime = "image/jpeg"

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

import io

from PIL import Image

from core.blob_store import MAX_IMAGE_BYTES
from core.gemini_enhance import (
    GeminiQuotaExceeded,
    enhance_jewellery_photo,
    gemini_configured,
    quota_blocked,
    quota_status,
)
from core.horde_enhance import enhance_with_horde, horde_enabled
from core.studio_remake import studio_remake
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
        enhance = True
    if watermark is None:
        watermark = True
    return bool(enhance), bool(watermark)


def _try_ai_fix(data: bytes, mime: str, notes: list):
    if gemini_configured() and not quota_blocked():
        try:
            improved = enhance_jewellery_photo(data, mime)
            notes.append("Gemini applied a studio catalogue look.")
            return improved, True
        except GeminiQuotaExceeded as exc:
            notes.append(str(exc) + " Trying free AI Horde next.")
        except Exception as exc:
            notes.append("Gemini skipped: " + str(exc)[:140] + " Trying free AI Horde next.")
    elif gemini_configured() and quota_blocked():
        wait = quota_status()["retry_after_seconds"]
        notes.append(f"Gemini quota cooling down ({wait}s). Trying free AI Horde.")

    if horde_enabled():
        try:
            improved = enhance_with_horde(data)
            notes.append("AI Horde applied a free studio img2img look.")
            return improved, True
        except Exception as exc:
            notes.append("AI Horde skipped: " + str(exc)[:140] + " Used a local studio remake.")
    else:
        notes.append("AI Horde is off in this environment. Used a local studio remake.")
    return studio_remake(data), False


def prepare_product_photo(data: bytes, mime: str, enhance: bool, watermark: bool):
    notes = []
    enhanced = False
    review = None

    # Never store the raw upload. Always produce a new studio JPEG first.
    remade = studio_remake(data)
    notes.append("Local studio remake applied so the original file is never stored.")

    if enhance:
        remade, enhanced = _try_ai_fix(data, mime or "image/jpeg", notes)
    else:
        notes.append("AI enhance was off; stored the studio remake, not the original.")

    if watermark:
        remade, review = apply_logo_watermark(remade, "image/jpeg")

    remade = jpeg_under_limit(remade)
    return {
        "data": remade,
        "mime": "image/jpeg",
        "enhanced": enhanced,
        "watermark": review,
        "notes": notes,
    }

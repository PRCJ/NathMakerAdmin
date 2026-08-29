import base64
import io
import os
import time

import httpx
from PIL import Image

DEFAULT_MODELS = (
    "gemini-3.1-flash-lite-image",
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image",
)
ENHANCE_PROMPT = (
    "Edit this jewellery photograph into a professional e-commerce catalog shot. "
    "Keep the exact same piece: shape, stones, metal colour, proportions, and design. "
    "Use soft studio lighting, a clean cream or light grey background, sharp focus, "
    "and luxury retail presentation like a high-end jewellery listing. "
    "Do not add extra jewellery, hands, models, text, logos, or watermarks. "
    "Photorealistic only. Square composition."
)

_quota_until = 0.0
_quota_reason = ""


class GeminiQuotaExceeded(RuntimeError):
    def __init__(self, message: str, retry_after: int = 90):
        super().__init__(message)
        self.retry_after = retry_after


def gemini_api_key() -> str:
    return (
        (os.environ.get("GEMINI_API_KEY") or "").strip()
        or (os.environ.get("GOOGLE_API_KEY") or "").strip()
        or (os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY") or "").strip()
    )


def gemini_configured() -> bool:
    return bool(gemini_api_key())


def reset_quota_cooldown():
    global _quota_until, _quota_reason
    _quota_until = 0.0
    _quota_reason = ""


def quota_blocked() -> bool:
    return time.time() < _quota_until


def mark_quota_cooldown(seconds: float, reason: str):
    global _quota_until, _quota_reason
    wait = max(30, int(seconds))
    _quota_until = time.time() + wait
    _quota_reason = reason


def quota_status():
    remaining = max(0, int(_quota_until - time.time()))
    return {
        "blocked": remaining > 0,
        "retry_after_seconds": remaining,
        "reason": _quota_reason if remaining > 0 else None,
    }


def gemini_models() -> list:
    preferred = (os.environ.get("GEMINI_IMAGE_MODEL") or "").strip()
    models = []
    if preferred:
        models.append(preferred)
    for name in DEFAULT_MODELS:
        if name not in models:
            models.append(name)
    return models


def shrink_for_gemini(image_bytes: bytes) -> bytes:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    longest = max(image.size)
    if longest > 1024:
        scale = 1024 / longest
        image = image.resize(
            (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
            Image.Resampling.LANCZOS,
        )
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=82, optimize=True)
    return buf.getvalue()


def _image_from_generate_content(data: dict) -> bytes:
    for candidate in data.get("candidates") or []:
        for part in (candidate.get("content") or {}).get("parts") or []:
            inline = part.get("inlineData") or part.get("inline_data") or {}
            raw = inline.get("data")
            if raw:
                return base64.b64decode(raw)
    raise RuntimeError("Gemini returned no image.")


def _retry_after_seconds(response: httpx.Response) -> int:
    header = (response.headers.get("retry-after") or "").strip()
    if header.isdigit():
        return min(int(header), 6 * 3600)
    text = (response.text or "").lower()
    if any(token in text for token in ("per day", "rpd", "billing", "plan", "quota")):
        return 6 * 3600
    return 90


def enhance_jewellery_photo(image_bytes: bytes, mime_type: str) -> bytes:
    key = gemini_api_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set in Vercel.")
    if quota_blocked():
        raise GeminiQuotaExceeded(
            "Gemini quota is cooling down; skipped to keep uploads moving.",
            retry_after=quota_status()["retry_after_seconds"],
        )

    jpeg = shrink_for_gemini(image_bytes)
    payload_image = base64.b64encode(jpeg).decode("ascii")
    model = gemini_models()[0]
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": ENHANCE_PROMPT},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": payload_image,
                        }
                    },
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": "1:1"},
        },
    }
    try:
        response = httpx.post(
            url,
            headers={"x-goog-api-key": key, "content-type": "application/json"},
            json=payload,
            timeout=45.0,
        )
    except Exception as exc:
        raise RuntimeError(f"Gemini request failed: {exc}") from exc

    if response.status_code == 429:
        wait = _retry_after_seconds(response)
        mark_quota_cooldown(wait, f"{model} returned 429")
        raise GeminiQuotaExceeded(
            "Gemini free/image quota was reached. Saved the original photo instead.",
            retry_after=wait,
        )
    if response.status_code >= 400:
        raise RuntimeError(f"Gemini enhance failed ({response.status_code}): {response.text[:300]}")
    return _image_from_generate_content(response.json())

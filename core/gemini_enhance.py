import base64
import io
import os

import httpx
from PIL import Image

DEFAULT_MODELS = (
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image",
    "gemini-2.5-flash-image-preview",
)
ENHANCE_PROMPT = (
    "Edit this jewellery photograph into a professional e-commerce catalog shot. "
    "Keep the exact same piece: shape, stones, metal colour, proportions, and design. "
    "Use soft studio lighting, a clean cream or light grey background, sharp focus, "
    "and luxury retail presentation like a high-end jewellery listing. "
    "Do not add extra jewellery, hands, models, text, logos, or watermarks. "
    "Photorealistic only. Square composition."
)


def gemini_api_key() -> str:
    return (
        (os.environ.get("GEMINI_API_KEY") or "").strip()
        or (os.environ.get("GOOGLE_API_KEY") or "").strip()
        or (os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY") or "").strip()
    )


def gemini_configured() -> bool:
    return bool(gemini_api_key())


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
    if longest > 1280:
        scale = 1280 / longest
        image = image.resize(
            (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
            Image.Resampling.LANCZOS,
        )
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=88, optimize=True)
    return buf.getvalue()


def _image_from_generate_content(data: dict) -> bytes:
    for candidate in data.get("candidates") or []:
        for part in (candidate.get("content") or {}).get("parts") or []:
            inline = part.get("inlineData") or part.get("inline_data") or {}
            raw = inline.get("data")
            if raw:
                return base64.b64decode(raw)
    raise RuntimeError("Gemini returned no image.")


def enhance_jewellery_photo(image_bytes: bytes, mime_type: str) -> bytes:
    key = gemini_api_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set in Vercel.")

    jpeg = shrink_for_gemini(image_bytes)
    payload_image = base64.b64encode(jpeg).decode("ascii")
    errors = []
    for model in gemini_models()[:2]:
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
            errors.append(f"{model}: {exc}")
            continue
        if response.status_code >= 400:
            errors.append(f"{model} ({response.status_code}): {response.text[:220]}")
            continue
        try:
            return _image_from_generate_content(response.json())
        except Exception as exc:
            errors.append(f"{model}: {exc}")
    raise RuntimeError("Gemini enhance failed. " + " | ".join(errors)[:400])

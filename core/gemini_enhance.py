import base64
import os

import httpx

GEMINI_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)
ENHANCE_PROMPT = (
    "Edit this jewellery photograph into a professional e-commerce catalog shot. "
    "Keep the exact same piece: shape, stones, metal colour, proportions, and design. "
    "Use soft studio lighting, a clean cream or light grey background, sharp focus, "
    "and luxury retail presentation like a high-end jewellery listing. "
    "Do not add extra jewellery, hands, models, text, logos, or watermarks. "
    "Photorealistic only. Square composition."
)


def gemini_configured() -> bool:
    return bool((os.environ.get("GEMINI_API_KEY") or "").strip())


def enhance_jewellery_photo(image_bytes: bytes, mime_type: str) -> bytes:
    key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set in Vercel.")

    mime = mime_type if mime_type in {"image/jpeg", "image/png", "image/webp", "image/gif"} else "image/jpeg"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": ENHANCE_PROMPT},
                    {
                        "inline_data": {
                            "mime_type": mime,
                            "data": base64.b64encode(image_bytes).decode("ascii"),
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
    response = httpx.post(
        GEMINI_ENDPOINT,
        headers={"x-goog-api-key": key, "content-type": "application/json"},
        json=payload,
        timeout=50.0,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"Gemini enhance failed ({response.status_code}): {response.text[:300]}"
        )

    data = response.json()
    for candidate in data.get("candidates") or []:
        for part in (candidate.get("content") or {}).get("parts") or []:
            inline = part.get("inlineData") or part.get("inline_data") or {}
            raw = inline.get("data")
            if raw:
                return base64.b64decode(raw)
    raise RuntimeError("Gemini returned no image. Check GEMINI_IMAGE_MODEL and API access.")

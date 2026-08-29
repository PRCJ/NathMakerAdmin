import base64
import io
import os
import time

import httpx
from PIL import Image

HORDE_URL = os.environ.get("AIHORDE_URL", "https://aihorde.net/api/v2").rstrip("/")
HORDE_PROMPT = (
    "professional ecommerce jewellery catalog photograph of the exact same jewellery, "
    "soft studio lighting, clean cream background, sharp focus, luxury retail, "
    "photorealistic ### watermark, text, logo, username, hands, extra jewellery, collage labels"
)


def horde_enabled() -> bool:
    if os.environ.get("TESTING") == "1":
        return False
    if (os.environ.get("AIHORDE_DISABLED") or "").strip() == "1":
        return False
    return True


def horde_api_key() -> str:
    return (os.environ.get("AIHORDE_API_KEY") or "0000000000").strip() or "0000000000"


def _headers():
    return {
        "apikey": horde_api_key(),
        "Client-Agent": "NathMakers:1.0:nathmakers.com",
        "Content-Type": "application/json",
    }


def _square_jpeg(image_bytes: bytes, size: int = 768) -> bytes:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    side = max(image.size)
    canvas = Image.new("RGB", (side, side), (245, 240, 232))
    canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
    canvas = canvas.resize((size, size), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    canvas.save(buf, format="JPEG", quality=82)
    return buf.getvalue()


def enhance_with_horde(image_bytes: bytes, timeout_seconds: float = 22.0) -> bytes:
    jpeg = _square_jpeg(image_bytes)
    payload = {
        "prompt": HORDE_PROMPT,
        "params": {
            "cfg_scale": 5.0,
            "denoising_strength": 0.34,
            "height": 768,
            "width": 768,
            "steps": 16,
            "n": 1,
            "sampler_name": "k_euler",
        },
        "nsfw": False,
        "censor_nsfw": True,
        "r2": True,
        "trusted_workers": False,
        "source_image": base64.b64encode(jpeg).decode("ascii"),
        "source_processing": "img2img",
        "models": ["AlbedoBase XL (SDXL)"],
    }
    started = time.time()
    submit = httpx.post(
        f"{HORDE_URL}/generate/async",
        headers=_headers(),
        json=payload,
        timeout=15.0,
    )
    if submit.status_code >= 400:
        raise RuntimeError(f"AI Horde rejected the job ({submit.status_code}): {submit.text[:200]}")
    job_id = (submit.json() or {}).get("id")
    if not job_id:
        raise RuntimeError("AI Horde did not return a job id.")

    while time.time() - started < timeout_seconds:
        check = httpx.get(
            f"{HORDE_URL}/generate/check/{job_id}",
            headers=_headers(),
            timeout=10.0,
        )
        if check.status_code >= 400:
            raise RuntimeError(f"AI Horde check failed ({check.status_code})")
        body = check.json() or {}
        if body.get("done"):
            status = httpx.get(
                f"{HORDE_URL}/generate/status/{job_id}",
                headers=_headers(),
                timeout=15.0,
            )
            status.raise_for_status()
            generations = (status.json() or {}).get("generations") or []
            if not generations:
                raise RuntimeError("AI Horde finished with no image.")
            img = generations[0].get("img")
            if not img:
                raise RuntimeError("AI Horde image payload was empty.")
            if img.startswith("http"):
                download = httpx.get(img, timeout=15.0, follow_redirects=True)
                download.raise_for_status()
                return download.content
            return base64.b64decode(img)
        time.sleep(2.0)
    raise RuntimeError("AI Horde timed out; using the studio remake instead.")

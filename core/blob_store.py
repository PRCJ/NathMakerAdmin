import os
import time

import httpx

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/pjpeg",
    "image/jfif",
    "image/png",
    "image/webp",
    "image/gif",
}
MAX_IMAGE_BYTES = 4 * 1024 * 1024
BLOB_API_URL = "https://vercel.com/api/blob"

_EXT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".jfif": "image/jpeg",
    ".pjpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def _blob_token() -> str:
    return (os.environ.get("BLOB_READ_WRITE_TOKEN") or "").strip()


def blob_configured() -> bool:
    return bool(_blob_token())


def blob_status():
    token_set = bool(_blob_token())
    store_set = bool((os.environ.get("BLOB_STORE_ID") or "").strip())
    return {
        "storage": "vercel_blob",
        "configured": token_set,
        "token_set": token_set,
        "store_id_set": store_set,
    }


def normalize_image_type(content_type: str, filename: str) -> str:
    mime = (content_type or "").split(";")[0].strip().lower()
    if mime in {"image/jpg", "image/pjpeg", "image/jfif"}:
        mime = "image/jpeg"
    if mime in ALLOWED_IMAGE_TYPES and mime != "image/jpg":
        return "image/jpeg" if mime == "image/jpeg" else mime
    ext = os.path.splitext(filename or "")[1].lower()
    return _EXT_TYPES.get(ext, mime)


def upload_image_bytes(data: bytes, filename: str, mime_type: str) -> str:
    token = _blob_token()
    if not token:
        raise RuntimeError(
            "Vercel Blob is not configured. Create a public Blob store in the "
            "Vercel project Storage tab so BLOB_READ_WRITE_TOKEN is set."
        )

    safe_name = os.path.basename(filename) or "image.jpg"
    pathname = f"products/{int(time.time())}_{safe_name}"
    headers = {
        "authorization": f"Bearer {token}",
        "x-api-version": "11",
        "x-content-type": mime_type,
        "x-vercel-blob-access": "public",
        "x-add-random-suffix": "1",
    }
    response = httpx.put(
        BLOB_API_URL,
        params={"pathname": pathname},
        headers=headers,
        content=data,
        timeout=30.0,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"Blob upload failed ({response.status_code}): {response.text[:300]}"
        )
    payload = response.json()
    url = payload.get("url")
    if not url:
        raise RuntimeError("Blob upload succeeded but no URL was returned.")
    return url


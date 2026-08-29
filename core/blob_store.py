import os
import time

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_BYTES = 4 * 1024 * 1024


def blob_configured() -> bool:
    return bool(
        (os.environ.get("BLOB_READ_WRITE_TOKEN") or "").strip()
        or (os.environ.get("BLOB_STORE_ID") or "").strip()
    )


def blob_status():
    token_set = bool((os.environ.get("BLOB_READ_WRITE_TOKEN") or "").strip())
    store_set = bool((os.environ.get("BLOB_STORE_ID") or "").strip())
    return {
        "storage": "vercel_blob",
        "configured": token_set or store_set,
        "token_set": token_set,
        "store_id_set": store_set,
    }


def upload_image_bytes(data: bytes, filename: str, mime_type: str) -> str:
    from vercel.blob import put

    if not blob_configured():
        raise RuntimeError(
            "Vercel Blob is not configured. Create a public Blob store in the "
            "Vercel project Storage tab so BLOB_READ_WRITE_TOKEN is set."
        )

    safe_name = os.path.basename(filename) or "image.jpg"
    pathname = f"products/{int(time.time())}_{safe_name}"
    result = put(
        pathname,
        data,
        access="public",
        content_type=mime_type,
        add_random_suffix=True,
    )
    return result.url

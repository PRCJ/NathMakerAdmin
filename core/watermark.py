import io
import os
from typing import Optional, Tuple

from PIL import Image, ImageDraw


def logo_path() -> Optional[str]:
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = (
        os.path.join(here, "assets", "logo.png"),
        os.path.join(here, "..", "public", "logo.png"),
        os.path.join(here, "..", "api", "assets", "logo.png"),
        os.path.join(os.getcwd(), "public", "logo.png"),
        os.path.join(os.getcwd(), "core", "assets", "logo.png"),
    )
    for candidate in candidates:
        path = os.path.abspath(candidate)
        if os.path.isfile(path):
            return path
    return None


def review_watermark(base: Image.Image, mark: Image.Image) -> dict:
    """Check that the brand mark is sized and contrasted like a catalogue watermark."""
    notes = []
    ok = True
    ratio = mark.width / max(base.width, 1)
    if ratio < 0.06:
        ok = False
        notes.append("Logo is too small (under 6% of image width).")
    elif ratio > 0.22:
        ok = False
        notes.append("Logo is too large (over 22% of image width).")
    else:
        notes.append("Logo size looks balanced.")

    pad = max(12, int(base.width * 0.02))
    left = max(base.width - mark.width - pad, 0)
    top = max(base.height - mark.height - pad, 0)
    corner = base.convert("RGB").crop((left, top, base.width, base.height)).convert("L")
    pixels = list(corner.getdata())
    avg = sum(pixels) / max(len(pixels), 1)
    if 90 < avg < 165:
        notes.append("Corner contrast is moderate; mark may blend on some photos.")
    else:
        notes.append("Corner contrast is strong enough for a faint mark.")
    return {"ok": ok, "notes": notes, "width_ratio": round(ratio, 3), "corner_brightness": round(avg, 1)}


def apply_logo_watermark(image_bytes: bytes, mime_type: str = "image/jpeg") -> Tuple[bytes, dict]:
    path = logo_path()
    if not path:
        return image_bytes, {
            "ok": False,
            "notes": ["NathMakers logo.png was not found; skipped watermark."],
            "width_ratio": 0,
        }

    base = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    logo = Image.open(path).convert("RGBA")
    target_w = max(48, int(base.width * 0.12))
    scale = target_w / max(logo.width, 1)
    logo = logo.resize((target_w, max(1, int(logo.height * scale))), Image.Resampling.LANCZOS)

    review = review_watermark(base, logo)
    pad = max(12, int(base.width * 0.02))
    x = base.width - logo.width - pad
    y = base.height - logo.height - pad

    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    if any("moderate" in note for note in review["notes"]):
        draw = ImageDraw.Draw(layer)
        margin = max(6, int(base.width * 0.008))
        draw.rounded_rectangle(
            (x - margin, y - margin, x + logo.width + margin, y + logo.height + margin),
            radius=max(6, margin),
            fill=(20, 16, 12, 90),
        )
        review["notes"].append("Added a faint backing so the mark stays readable.")

    alpha = logo.split()[-1].point(lambda p: int(p * 0.42))
    logo.putalpha(alpha)
    layer.paste(logo, (x, y), logo)
    out = Image.alpha_composite(base, layer).convert("RGB")

    buf = io.BytesIO()
    out.save(buf, format="JPEG", quality=90)
    return buf.getvalue(), review

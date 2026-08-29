import io

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps

WHITE = (255, 255, 255)


def _border_background(rgb: np.ndarray) -> np.ndarray:
    border = np.concatenate(
        [rgb[0, :], rgb[-1, :], rgb[:, 0], rgb[:, -1]],
        axis=0,
    )
    return np.median(border, axis=0)


def _remove_border_cloth(mask: np.ndarray, rgb: np.ndarray) -> np.ndarray:
    """Drop large low-saturation regions that touch the frame (tablecloth, velvet slabs)."""
    num, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if num <= 1:
        return mask
    height, width = mask.shape
    total = height * width
    keep = np.zeros_like(mask)
    sat = rgb.max(axis=2).astype(np.int16) - rgb.min(axis=2).astype(np.int16)
    luma = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    for index in range(1, num):
        area = int(stats[index, cv2.CC_STAT_AREA])
        if area < 40:
            continue
        component = labels == index
        touches_border = (
            component[0, :].any()
            or component[-1, :].any()
            or component[:, 0].any()
            or component[:, -1].any()
        )
        median_sat = float(np.median(sat[component]))
        median_luma = float(np.median(luma[component]))
        if touches_border and area > total * 0.02 and (
            median_sat < 65 or (median_luma > 145 and median_sat < 85)
        ):
            continue
        keep[component] = 255
    return keep


def _jewellery_mask(rgb: np.ndarray) -> np.ndarray:
    """True where the jewellery is. Biased to keep the full outline."""
    height, width, _ = rgb.shape
    bg = _border_background(rgb)
    pixels = rgb.astype(np.int16)
    dist = np.abs(pixels - bg.astype(np.int16)).sum(axis=2)
    luma = 0.299 * pixels[:, :, 0] + 0.587 * pixels[:, :, 1] + 0.114 * pixels[:, :, 2]
    sat = pixels.max(axis=2) - pixels.min(axis=2)
    bg_luma = float(0.299 * bg[0] + 0.587 * bg[1] + 0.114 * bg[2])

    if bg_luma < 95:
        # Dark cloth: keep metal, stones, pearls. Leave velvet out.
        foreground = (sat > 26) | (luma > 78)
        dark_cloth = (luma < 50) & (sat < 28)
    else:
        thresh = max(40, int(np.percentile(dist[0:3, :], 70)) + 16)
        foreground = (dist >= thresh) | (sat > 38) | (luma < bg_luma - 28)
        dark_cloth = None

    mask = foreground.astype(np.uint8) * 255
    if dark_cloth is not None:
        mask[dark_cloth] = 0
    close_r = max(2, min(height, width) // 220)
    dilate_r = max(2, min(height, width) // 160)
    close_k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_r * 2 + 1, close_r * 2 + 1))
    dilate_k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_r * 2 + 1, dilate_r * 2 + 1))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, close_k)
    # Grow a few pixels only so the outline is complete, not a cloth halo.
    mask = cv2.dilate(mask, dilate_k, iterations=1)
    if dark_cloth is not None:
        mask[dark_cloth] = 0
        mask = cv2.dilate(mask, close_k, iterations=1)
    mask = _remove_border_cloth(mask, rgb)
    return mask


def isolate_jewellery(image: Image.Image) -> Image.Image:
    """Return RGBA: jewellery only, background fully transparent."""
    rgb = np.array(image.convert("RGB"))
    mask = _jewellery_mask(rgb)
    coverage = float(mask.mean()) / 255.0
    if coverage < 0.004 or coverage > 0.94:
        rgba = np.dstack([rgb, np.full(mask.shape, 255, dtype=np.uint8)])
        return Image.fromarray(rgba, "RGBA")

    # Crisp outline: light feather only, after the silhouette was dilated.
    alpha = cv2.GaussianBlur(mask, (3, 3), 0)
    rgba = np.dstack([rgb, alpha])
    return Image.fromarray(rgba, "RGBA")


def _crop_to_object(rgba: Image.Image, pad_ratio: float = 0.12) -> Image.Image:
    alpha = rgba.split()[-1]
    box = alpha.getbbox()
    if not box:
        return rgba
    left, top, right, bottom = box
    pad = max(16, int(max(right - left, bottom - top) * pad_ratio))
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(rgba.width, right + pad)
    bottom = min(rgba.height, bottom + pad)
    return rgba.crop((left, top, right, bottom))


def place_on_white(rgba: Image.Image) -> Image.Image:
    piece = _crop_to_object(rgba)
    side = max(piece.size)
    margin = max(28, int(side * 0.10))
    canvas_size = side + margin * 2
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (255, 255, 255, 255))
    ox = (canvas_size - piece.width) // 2
    oy = (canvas_size - piece.height) // 2
    canvas.alpha_composite(piece, (ox, oy))
    return canvas.convert("RGB")


def studio_remake(image_bytes: bytes) -> bytes:
    """Identify jewellery, make the background transparent, then place it on white."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = ImageOps.exif_transpose(image)
    longest = max(image.size)
    if longest > 1400:
        scale = 1400 / longest
        image = image.resize(
            (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
            Image.Resampling.LANCZOS,
        )

    isolated = isolate_jewellery(image)
    on_white = place_on_white(isolated)
    on_white = ImageEnhance.Contrast(on_white).enhance(1.04)
    on_white = ImageEnhance.Sharpness(on_white).enhance(1.05)

    buf = io.BytesIO()
    on_white.save(buf, format="JPEG", quality=93, optimize=True)
    return buf.getvalue()

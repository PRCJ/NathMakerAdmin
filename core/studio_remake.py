import io

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps

WHITE = (255, 255, 255)


def _channels(rgb: np.ndarray):
    pixels = rgb.astype(np.int16)
    red, green, blue = pixels[:, :, 0], pixels[:, :, 1], pixels[:, :, 2]
    sat = np.maximum(np.maximum(red, green), blue) - np.minimum(np.minimum(red, green), blue)
    luma = 0.299 * red + 0.587 * green + 0.114 * blue
    return red, green, blue, sat, luma


def _skin_mask(red, green, blue, sat, luma) -> np.ndarray:
    return (
        (red > 95)
        & (green > 45)
        & (blue > 70)
        & ((red - green) > 16)
        & ((red - green) < 80)
        & ((green - blue) < 45)
        & (sat < 90)
        & (luma > 75)
        & (luma < 225)
    )


def _border_background(rgb: np.ndarray) -> np.ndarray:
    border = np.concatenate(
        [rgb[0, :], rgb[-1, :], rgb[:, 0], rgb[:, -1]],
        axis=0,
    )
    return np.median(border, axis=0)


def _remove_border_cloth(mask: np.ndarray, rgb: np.ndarray) -> np.ndarray:
    num, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if num <= 1:
        return mask
    height, width = mask.shape
    total = height * width
    keep = np.zeros_like(mask)
    red, green, blue, sat, luma = _channels(rgb)
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


def _cloth_jewellery_mask(rgb: np.ndarray) -> np.ndarray:
    """Jewellery on a table/velvet backdrop."""
    height, width, _ = rgb.shape
    bg = _border_background(rgb)
    red, green, blue, sat, luma = _channels(rgb)
    dist = np.abs(rgb.astype(np.int16) - bg.astype(np.int16)).sum(axis=2)
    bg_luma = float(0.299 * bg[0] + 0.587 * bg[1] + 0.114 * bg[2])

    if bg_luma < 95:
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
    mask = cv2.dilate(mask, dilate_k, iterations=1)
    if dark_cloth is not None:
        mask[dark_cloth] = 0
        mask = cv2.dilate(mask, close_k, iterations=1)
    return _remove_border_cloth(mask, rgb)


def _model_jewellery_mask(rgb: np.ndarray) -> np.ndarray:
    """Jewellery held in a hand or worn in a lifestyle shot."""
    height, width, _ = rgb.shape
    red, green, blue, sat, luma = _channels(rgb)
    skin = _skin_mask(red, green, blue, sat, luma)
    kundan = (
        (red > 168)
        & (red > green + 48)
        & (red > blue + 48)
        & (sat > 62)
        & (luma > 86)
        & (luma < 205)
        & (~skin)
    )
    stone = kundan.astype(np.uint8) * 255
    stone = cv2.morphologyEx(
        stone,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21)),
    )
    stone = cv2.morphologyEx(
        stone,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
    )
    num, _labels, stats, cents = cv2.connectedComponentsWithStats(stone, connectivity=8)
    clusters = []
    for index in range(1, num):
        area = int(stats[index, cv2.CC_STAT_AREA])
        box_w = int(stats[index, cv2.CC_STAT_WIDTH])
        box_h = int(stats[index, cv2.CC_STAT_HEIGHT])
        cx, cy = cents[index]
        fill = area / max(box_w * box_h, 1)
        if area < 200 or area > 20000:
            continue
        if cy < height * 0.30 or cy > height * 0.70:
            continue
        if box_w > width * 0.50 or box_h > height * 0.35:
            continue
        if fill < 0.30:
            continue
        if cx < width * 0.10 or cx > width * 0.90:
            continue
        clusters.append((area, int(cx), int(cy), max(box_w, box_h)))
    clusters.sort(reverse=True)

    gold = (
        (red > 148)
        & (green > 118)
        & (blue < 125)
        & ((green - blue) > 26)
        & (sat > 45)
        & (~skin)
    )
    gem_green = (green > 75) & (green > red + 6) & (green > blue) & (sat > 35) & (~skin)
    metal = gold | kundan
    near_metal = cv2.dilate(
        metal.astype(np.uint8) * 255,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
        iterations=1,
    ) > 0
    pearl = (luma > 155) & (sat < 58) & (red > 135) & near_metal & (~skin)

    keep = np.zeros((height, width), np.uint8)
    for _area, cx, cy, span in clusters[:2]:
        radius = int(max(span * 0.48, 36)) + 6
        yy, xx = np.ogrid[:height, :width]
        circle = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius ** 2
        drop = (yy > cy) & (
            (xx - cx) ** 2 + (yy - (cy + int(radius * 0.42))) ** 2
            <= int((radius * 0.40) ** 2)
        )
        region = circle | drop
        local = (gold | kundan | gem_green | pearl) & region & (~skin)
        keep[local] = 255

    if keep.mean() < 2:
        material = ((gold | kundan | gem_green | pearl) & (~skin)).astype(np.uint8) * 255
        material = cv2.morphologyEx(
            material,
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        )
        keep = _remove_border_cloth(material, rgb)

    keep = cv2.morphologyEx(
        keep,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
    )
    keep = cv2.dilate(
        keep,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4, 4)),
        iterations=1,
    )
    num, labels, stats, _ = cv2.connectedComponentsWithStats(keep, connectivity=8)
    cleaned = np.zeros_like(keep)
    for index in range(1, num):
        component = labels == index
        if int(stats[index, cv2.CC_STAT_AREA]) < 50:
            continue
        if float(skin[component].mean()) > 0.45 and float(kundan[component].mean()) < 0.04:
            continue
        cleaned[component] = 255
    return cleaned


def _jewellery_mask(rgb: np.ndarray) -> np.ndarray:
    _red, _green, _blue, sat, luma = _channels(rgb)
    skin_frac = float(_skin_mask(_red, _green, _blue, sat, luma).mean())
    if skin_frac > 0.10:
        return _model_jewellery_mask(rgb)
    return _cloth_jewellery_mask(rgb)


def isolate_jewellery(image: Image.Image) -> Image.Image:
    """Return RGBA: jewellery only, background fully transparent."""
    rgb = np.array(image.convert("RGB"))
    mask = _jewellery_mask(rgb)
    coverage = float(mask.mean()) / 255.0
    if coverage < 0.004 or coverage > 0.94:
        rgba = np.dstack([rgb, np.full(mask.shape, 255, dtype=np.uint8)])
        return Image.fromarray(rgba, "RGBA")

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

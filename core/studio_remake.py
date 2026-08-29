import io

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps


def _is_dark_backdrop(red: int, green: int, blue: int) -> bool:
    luma = 0.299 * red + 0.587 * green + 0.114 * blue
    sat = max(red, green, blue) - min(red, green, blue)
    return luma < 52 and sat < 28


def _replace_dark_backdrop(image: Image.Image, cream=(245, 240, 232)) -> Image.Image:
    """Swap near-black cloth/velvet for cream. Leave jewellery RGB untouched."""
    width, height = image.size
    src = image.load()
    out = image.copy()
    dest = out.load()
    hits = 0
    total = width * height
    for y in range(height):
        for x in range(width):
            pixel = src[x, y]
            if _is_dark_backdrop(*pixel[:3]):
                dest[x, y] = cream
                hits += 1
    if hits < total * 0.12:
        return image
    return out.filter(ImageFilter.SMOOTH)


def studio_remake(image_bytes: bytes) -> bytes:
    """Catalogue presentation wrap. Does not redraw or morph the jewellery."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = ImageOps.exif_transpose(image)
    longest = max(image.size)
    if longest > 1600:
        scale = 1600 / longest
        image = image.resize(
            (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
            Image.Resampling.LANCZOS,
        )

    image = _replace_dark_backdrop(image)
    image = ImageEnhance.Contrast(image).enhance(1.06)
    image = ImageEnhance.Sharpness(image).enhance(1.08)

    side = max(image.size)
    pad = max(20, int(side * 0.06))
    canvas_size = side + pad * 2
    canvas = Image.new("RGB", (canvas_size, canvas_size), (245, 240, 232))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, canvas_size, int(canvas_size * 0.42)), fill=(250, 246, 240))
    ox = (canvas_size - image.width) // 2
    oy = (canvas_size - image.height) // 2
    canvas.paste(image, (ox, oy))

    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="JPEG", quality=92, optimize=True)
    return buf.getvalue()

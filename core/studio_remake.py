import io

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps


def _white_balance(image: Image.Image) -> Image.Image:
    pixels = list(image.getdata())
    count = max(len(pixels), 1)
    avg = [sum(p[i] for p in pixels) / count for i in range(3)]
    target = (avg[0] + avg[1] + avg[2]) / 3.0 or 1.0
    scale = [target / (channel or 1.0) for channel in avg]
    balanced = [
        (
            min(255, max(0, int(p[0] * scale[0]))),
            min(255, max(0, int(p[1] * scale[1]))),
            min(255, max(0, int(p[2] * scale[2]))),
        )
        for p in pixels
    ]
    out = Image.new("RGB", image.size)
    out.putdata(balanced)
    return out


def _corner_background(image: Image.Image):
    width, height = image.size
    samples = [
        image.getpixel((2, 2)),
        image.getpixel((width - 3, 2)),
        image.getpixel((2, height - 3)),
        image.getpixel((width - 3, height - 3)),
    ]
    avg = tuple(int(sum(sample[i] for sample in samples) / 4) for i in range(3))
    spread = max(
        max(abs(sample[i] - avg[i]) for sample in samples)
        for i in range(3)
    )
    return avg, spread


def _cutout_on_studio(image: Image.Image, bg, tolerance: int) -> Image.Image:
    width, height = image.size
    src = image.load()
    rgba = Image.new("RGBA", image.size)
    dest = rgba.load()
    br, bgc, bb = bg
    for y in range(height):
        for x in range(width):
            red, green, blue = src[x, y]
            dist = abs(red - br) + abs(green - bgc) + abs(blue - bb)
            if dist < tolerance:
                dest[x, y] = (red, green, blue, 0)
            else:
                alpha = min(255, (dist - tolerance) * 6)
                dest[x, y] = (red, green, blue, alpha)
    return rgba.filter(ImageFilter.SMOOTH)


def studio_remake(image_bytes: bytes) -> bytes:
    """Always return a new studio catalogue JPEG. Never the original bytes."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = ImageOps.exif_transpose(image)
    longest = max(image.size)
    if longest > 1400:
        scale = 1400 / longest
        image = image.resize(
            (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
            Image.Resampling.LANCZOS,
        )
    image = _white_balance(image)
    image = ImageEnhance.Contrast(image).enhance(1.16)
    image = ImageEnhance.Color(image).enhance(1.08)
    image = ImageEnhance.Sharpness(image).enhance(1.28)

    bg, spread = _corner_background(image)
    subject = image.convert("RGBA")
    if spread < 28:
        subject = _cutout_on_studio(image, bg, tolerance=max(36, spread + 18))

    side = max(subject.size)
    pad = max(24, int(side * 0.08))
    canvas_size = side + pad * 2
    canvas = Image.new("RGB", (canvas_size, canvas_size), (245, 240, 232))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, canvas_size, canvas_size // 2), fill=(250, 246, 240))
    shadow = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    ox = (canvas_size - subject.width) // 2
    oy = (canvas_size - subject.height) // 2
    sdraw.ellipse(
        (ox + 12, oy + subject.height - 18, ox + subject.width - 12, oy + subject.height + 22),
        fill=(40, 28, 18, 45),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), shadow)
    canvas.paste(subject, (ox, oy), subject)
    finished = canvas.convert("RGB")
    finished = ImageEnhance.Brightness(finished).enhance(1.03)

    buf = io.BytesIO()
    finished.save(buf, format="JPEG", quality=90, optimize=True)
    return buf.getvalue()

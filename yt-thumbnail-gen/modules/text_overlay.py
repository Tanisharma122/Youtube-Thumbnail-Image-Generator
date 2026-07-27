"""
Burns a bold, YouTube-style title (with a stroke outline for readability
over any background) onto the generated thumbnail using Pillow.
"""
import os
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = os.environ.get("OVERLAY_FONT_PATH", "")  # optional custom .ttf path


def _load_font(size: int):
    candidates = [
        FONT_PATH,
        # Windows Fonts
        "C:\\Windows\\Fonts\\impact.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\segoeuib.ttf",
        # Linux Fonts
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        # macOS Fonts
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]
    for path in candidates:
        if path and os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def add_title_text(image: Image.Image, text: str) -> Image.Image:
    image = image.convert("RGB")
    draw = ImageDraw.Draw(image)

    w, h = image.size
    font_size = int(h * 0.13)
    font = _load_font(font_size)

    # wrap text to fit width (~90% of image)
    max_width = int(w * 0.9)
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    # position block near the bottom third
    line_height = font_size * 1.15
    total_height = line_height * len(lines)
    y = h - total_height - (h * 0.06)

    stroke_width = max(2, font_size // 18)

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (w - text_w) / 2
        draw.text(
            (x, y), line, font=font,
            fill="white", stroke_width=stroke_width, stroke_fill="black"
        )
        y += line_height

    return image

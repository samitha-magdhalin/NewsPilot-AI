
from pathlib import Path
from urllib.parse import urlparse
import math
import re
import textwrap

from PIL import Image, ImageDraw, ImageFont, ImageFilter


# ============================================================
# NewsPilot AI — News Graphic Generator
# Creates attractive, readable editorial graphics using Pillow.
# No external image API key is required.
# ============================================================

STYLES = [
    "Editorial Magazine",
    "Photojournalism",
    "Breaking News",
    "Technology & Data",
    "Minimal Report",
    "Illustrated Feature",
]

PALETTES = {
    "Editorial Magazine": {
        "background": "#10182B",
        "panel": "#17233A",
        "accent": "#FFCA68",
        "accent2": "#F27D72",
        "text": "#FFFFFF",
        "muted": "#C5CFDF",
    },
    "Photojournalism": {
        "background": "#152B2A",
        "panel": "#203B38",
        "accent": "#E9D5A5",
        "accent2": "#78C8B5",
        "text": "#FFFFFF",
        "muted": "#C9DCD6",
    },
    "Breaking News": {
        "background": "#15151B",
        "panel": "#24242D",
        "accent": "#FF4B55",
        "accent2": "#FFB84D",
        "text": "#FFFFFF",
        "muted": "#D2D2DB",
    },
    "Technology & Data": {
        "background": "#091A35",
        "panel": "#10294B",
        "accent": "#5DE1FF",
        "accent2": "#9C8AFF",
        "text": "#FFFFFF",
        "muted": "#C1D7F2",
    },
    "Minimal Report": {
        "background": "#F4F0E8",
        "panel": "#FFFFFF",
        "accent": "#2459D3",
        "accent2": "#E76D50",
        "text": "#182238",
        "muted": "#566174",
    },
    "Illustrated Feature": {
        "background": "#211A3B",
        "panel": "#302650",
        "accent": "#FFD166",
        "accent2": "#FF7D9C",
        "text": "#FFFFFF",
        "muted": "#D8CFF1",
    },
}


def _font(size, bold=False):
    """Load a font that works on Windows and common Linux servers."""
    size = max(10, int(size))

    if bold:
        candidates = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]
    else:
        candidates = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]

    for font_path in candidates:
        try:
            if Path(font_path).exists():
                return ImageFont.truetype(font_path, size=size)
        except OSError:
            continue

    return ImageFont.load_default()


def _text_width(draw, text, font):
    """Return the pixel width of a text string."""
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def _text_height(draw, text, font):
    """Return the pixel height of a text string."""
    box = draw.textbbox((0, 0), text or "Ag", font=font)
    return box[3] - box[1]


def _wrap(draw, text, font, max_width):
    """Wrap text according to the actual rendered font width."""
    text = re.sub(r"\s+", " ", str(text or "")).strip()

    if not text:
        return []

    words = text.split()
    lines = []
    current = ""

    for word in words:
        candidate = word if not current else current + " " + word

        if _text_width(draw, candidate, font) <= max_width:
            current = candidate
            continue

        if current:
            lines.append(current)

        # Split an unusually long word rather than letting it overflow.
        if _text_width(draw, word, font) > max_width:
            piece = ""

            for character in word:
                test = piece + character

                if _text_width(draw, test, font) <= max_width:
                    piece = test
                else:
                    if piece:
                        lines.append(piece)
                    piece = character

            current = piece
        else:
            current = word

    if current:
        lines.append(current)

    return lines


def _gradient(size, top_color, bottom_color):
    """Create a smooth vertical RGB gradient."""
    width, height = size
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)

    def rgb(hex_color):
        value = hex_color.lstrip("#")
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))

    top = rgb(top_color)
    bottom = rgb(bottom_color)

    for y in range(height):
        ratio = y / max(1, height - 1)
        color = tuple(
            int(top[i] * (1 - ratio) + bottom[i] * ratio)
            for i in range(3)
        )
        draw.line((0, y, width, y), fill=color)

    return image


def _rounded_rectangle(draw, xy, radius, fill, outline=None, width=1):
    """Draw a rounded rectangle with a consistent Pillow interface."""
    draw.rounded_rectangle(
        xy,
        radius=radius,
        fill=fill,
        outline=outline,
        width=width,
    )


def _motif(image, style, palette):
    """Draw decorative illustrations in the upper visual area."""
    width, height = image.size
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    accent = palette["accent"]
    accent2 = palette["accent2"]

    def rgba(color, alpha=255):
        value = color.lstrip("#")
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)

    # Subtle background rings create depth without distracting from text.
    center_x = int(width * 0.77)
    center_y = int(height * 0.17)

    for index in range(5):
        radius = int(width * (0.10 + index * 0.055))
        draw.ellipse(
            (
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
            ),
            outline=rgba(accent, max(12, 45 - index * 6)),
            width=max(2, width // 360),
        )

    if style == "Technology & Data":
        # Glowing data nodes and connecting lines.
        points = [
            (0.12, 0.12), (0.28, 0.08), (0.40, 0.19),
            (0.56, 0.10), (0.70, 0.21), (0.88, 0.11),
            (0.20, 0.30), (0.43, 0.34), (0.66, 0.34),
            (0.84, 0.30),
        ]
        pixel_points = [
            (int(x * width), int(y * height)) for x, y in points
        ]

        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4), (4, 5),
            (0, 6), (2, 7), (4, 8), (5, 9),
            (6, 7), (7, 8), (8, 9),
        ]

        for start, end in connections:
            draw.line(
                (*pixel_points[start], *pixel_points[end]),
                fill=rgba(accent, 100),
                width=max(2, width // 500),
            )

        for index, point in enumerate(pixel_points):
            radius = max(5, width // 90)
            color = accent if index % 2 == 0 else accent2
            draw.ellipse(
                (
                    point[0] - radius,
                    point[1] - radius,
                    point[0] + radius,
                    point[1] + radius,
                ),
                fill=rgba(color, 220),
            )

    elif style == "Breaking News":
        # Strong diagonal bars and an attention-grabbing circular mark.
        draw.polygon(
            [
                (int(width * 0.63), 0),
                (int(width * 0.91), 0),
                (int(width * 0.57), int(height * 0.36)),
                (int(width * 0.39), int(height * 0.36)),
            ],
            fill=rgba(accent, 45),
        )
        draw.polygon(
            [
                (int(width * 0.88), 0),
                (width, 0),
                (width, int(height * 0.25)),
                (int(width * 0.73), int(height * 0.36)),
            ],
            fill=rgba(accent2, 55),
        )

        radius = int(width * 0.075)
        x, y = int(width * 0.80), int(height * 0.19)
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=rgba(accent, 235),
        )
        bang_font = _font(int(width * 0.09), bold=True)
        draw.text(
            (x, y - int(width * 0.006)),
            "!",
            font=bang_font,
            fill=rgba("#FFFFFF"),
            anchor="mm",
        )

    elif style == "Illustrated Feature":
        # Overlapping organic shapes for a more playful magazine feel.
        draw.ellipse(
            (
                int(width * 0.58),
                int(height * 0.035),
                int(width * 0.91),
                int(height * 0.33),
            ),
            fill=rgba(accent, 180),
        )
        draw.ellipse(
            (
                int(width * 0.73),
                int(height * 0.12),
                int(width * 1.02),
                int(height * 0.39),
            ),
            fill=rgba(accent2, 175),
        )
        draw.ellipse(
            (
                int(width * 0.66),
                int(height * 0.19),
                int(width * 0.80),
                int(height * 0.33),
            ),
            fill=rgba(palette["panel"], 240),
        )

        # Decorative sparkles.
        for x_ratio, y_ratio in [
            (0.14, 0.12), (0.36, 0.25), (0.48, 0.09), (0.91, 0.35)
        ]:
            x = int(width * x_ratio)
            y = int(height * y_ratio)
            radius = max(4, width // 100)
            draw.line(
                (x - radius, y, x + radius, y),
                fill=rgba(accent, 220),
                width=3,
            )
            draw.line(
                (x, y - radius, x, y + radius),
                fill=rgba(accent, 220),
                width=3,
            )

    elif style == "Photojournalism":
        # Layered horizon and landscape silhouettes.
        draw.ellipse(
            (
                int(width * 0.70),
                int(height * 0.06),
                int(width * 0.88),
                int(height * 0.24),
            ),
            fill=rgba(accent, 180),
        )
        draw.polygon(
            [
                (0, int(height * 0.28)),
                (int(width * 0.20), int(height * 0.16)),
                (int(width * 0.39), int(height * 0.29)),
                (int(width * 0.57), int(height * 0.14)),
                (int(width * 0.79), int(height * 0.28)),
                (width, int(height * 0.17)),
                (width, int(height * 0.43)),
                (0, int(height * 0.43)),
            ],
            fill=rgba(accent2, 90),
        )

    else:
        # Editorial and minimal styles get abstract shapes and fine lines.
        draw.arc(
            (
                int(width * 0.59),
                int(height * 0.03),
                int(width * 0.98),
                int(height * 0.38),
            ),
            start=190,
            end=350,
            fill=rgba(accent, 220),
            width=max(3, width // 180),
        )
        draw.line(
            (
                int(width * 0.08),
                int(height * 0.29),
                int(width * 0.47),
                int(height * 0.29),
            ),
            fill=rgba(accent, 160),
            width=max(2, width // 360),
        )

    # A light blur softens only the decorative artwork.
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=max(0.4, width / 1800)))
    image_rgba = image.convert("RGBA")
    image_rgba.alpha_composite(overlay)
    return image_rgba.convert("RGB")


def _draw_wrapped_text(
    draw,
    text,
    x,
    y,
    max_width,
    font,
    fill,
    max_lines=None,
    line_spacing=1.22,
):
    """Draw wrapped text and return the next vertical position."""
    lines = _wrap(draw, text, font, max_width)

    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            last = lines[-1]
            while last and _text_width(draw, last + "…", font) > max_width:
                last = last[:-1].rstrip()
            lines[-1] = last.rstrip(" ,;:-") + "…"

    line_height = int(_text_height(draw, "Ag", font) * line_spacing)

    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height

    return y, len(lines)


def _shorten(text, max_chars):
    text = re.sub(r"\s+", " ", str(text or "")).strip()

    if len(text) <= max_chars:
        return text

    shortened = text[: max_chars - 1].rsplit(" ", 1)[0].rstrip()

    if not shortened:
        shortened = text[: max_chars - 1]

    return shortened + "…"


def _source_label(source_url, publisher):
    """Use the source domain where available; otherwise use the publisher."""
    if source_url:
        try:
            domain = urlparse(source_url).netloc.lower()
            domain = re.sub(r"^www\.", "", domain)
            if domain:
                return domain
        except (ValueError, TypeError):
            pass

    return re.sub(r"\s+", " ", str(publisher or "News source")).strip()


def make_graphic(
    headline,
    summary,
    publisher="News source",
    published_date="",
    source_url="",
    status="INSUFFICIENT_EVIDENCE",
    output_path="output/newspilot.png",
    size=(1080, 1350),
    style="Editorial Magazine",
):
    """
    Generate a polished, readable news graphic as a PNG.

    Parameters match the NewsPilot AI graphic generator interface.

    Returns:
        pathlib.Path: path to the generated PNG file.
    """
    width, height = size

    if width < 320 or height < 400:
        raise ValueError("Graphic size must be at least 320 x 400 pixels.")

    style = style if style in PALETTES else "Editorial Magazine"
    palette = PALETTES[style]

    headline = re.sub(r"\s+", " ", str(headline or "")).strip()
    summary = re.sub(r"\s+", " ", str(summary or "")).strip()

    if not headline:
        headline = "Today's News, Clearly Explained"

    # A graphic should not present a headline as though it were a summary.
    if summary and headline.casefold().strip(" .!?") == summary.casefold().strip(" .!?"):
        summary = ""

    image = _gradient(
        size,
        palette["background"],
        palette["panel"],
    )
    image = _motif(image, style, palette)
    draw = ImageDraw.Draw(image)

    scale = width / 1080
    pad = int(width * 0.075)
    content_width = width - 2 * pad

    # Top section: branding and editorial illustration.
    brand_font = _font(int(width * 0.027), bold=True)
    tiny_font = _font(int(width * 0.019))
    label_font = _font(int(width * 0.021), bold=True)

    brand_y = int(height * 0.045)

    draw.text(
        (pad, brand_y),
        "NEWSPILOT",
        font=brand_font,
        fill=palette["text"],
    )

    brand_width = _text_width(draw, "NEWSPILOT", brand_font)
    draw.rounded_rectangle(
        (
            pad + brand_width + int(width * 0.012),
            brand_y + int(width * 0.006),
            pad + brand_width + int(width * 0.048),
            brand_y + int(width * 0.027),
        ),
        radius=int(width * 0.006),
        fill=palette["accent"],
    )

    draw.text(
        (pad, int(height * 0.085)),
        "THE STORY BEHIND THE HEADLINE",
        font=tiny_font,
        fill=palette["muted"],
    )

    # Main text panel sits below the decorative top section.
    panel_top = int(height * 0.365)
    panel_bottom = height - int(height * 0.055)
    panel_radius = int(width * 0.035)

    shadow_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_draw.rounded_rectangle(
        (
            pad - int(width * 0.006),
            panel_top + int(height * 0.009),
            width - pad + int(width * 0.006),
            panel_bottom + int(height * 0.008),
        ),
        radius=panel_radius,
        fill=(0, 0, 0, 65),
    )
    shadow_layer = shadow_layer.filter(
        ImageFilter.GaussianBlur(radius=max(2, int(width * 0.012)))
    )
    image = Image.alpha_composite(
        image.convert("RGBA"), shadow_layer
    ).convert("RGB")
    draw = ImageDraw.Draw(image)

    _rounded_rectangle(
        draw,
        (pad, panel_top, width - pad, panel_bottom),
        radius=panel_radius,
        fill=palette["panel"],
    )

    # Small accent strip makes the panel feel like an editorial cover.
    strip_width = int(width * 0.012)
    _rounded_rectangle(
        draw,
        (
            pad,
            panel_top + int(height * 0.035),
            pad + strip_width,
            panel_top + int(height * 0.13),
        ),
        radius=max(2, strip_width // 2),
        fill=palette["accent"],
    )

    inner_x = pad + int(width * 0.045)
    inner_width = width - 2 * inner_x
    text_y = panel_top + int(height * 0.045)

    # Category/status pill.
    category = (
        "BREAKING NEWS"
        if "BREAKING" in str(status).upper()
        else "NEWS BRIEFING"
    )

    pill_font = _font(int(width * 0.020), bold=True)
    pill_padding_x = int(width * 0.018)
    pill_padding_y = int(width * 0.010)
    pill_width = _text_width(draw, category, pill_font) + pill_padding_x * 2
    pill_height = _text_height(draw, category, pill_font) + pill_padding_y * 2

    _rounded_rectangle(
        draw,
        (
            inner_x,
            text_y,
            inner_x + pill_width,
            text_y + pill_height,
        ),
        radius=pill_height // 2,
        fill=palette["accent"],
    )

    draw.text(
        (inner_x + pill_padding_x, text_y + pill_padding_y - 1),
        category,
        font=pill_font,
        fill=palette["background"],
    )

    text_y += pill_height + int(height * 0.030)

    # Large headline. Shrink font only as much as needed to fit.
    title_font_size = int(width * 0.066)
    title_max_height = int(height * 0.235)
    title_max_lines = 5
    title_lines = []

    while title_font_size >= int(width * 0.038):
        title_font = _font(title_font_size, bold=True)
        title_lines = _wrap(draw, headline, title_font, inner_width)
        line_height = int(_text_height(draw, "Ag", title_font) * 1.10)

        if (
            len(title_lines) <= title_max_lines
            and len(title_lines) * line_height <= title_max_height
        ):
            break

        title_font_size -= max(1, int(width * 0.002))

    title_font = _font(title_font_size, bold=True)
    title_line_height = int(_text_height(draw, "Ag", title_font) * 1.10)

    if len(title_lines) > title_max_lines:
        title_lines = title_lines[:title_max_lines]
        last = title_lines[-1]
        while last and _text_width(draw, last + "…", title_font) > inner_width:
            last = last[:-1].rstrip()
        title_lines[-1] = last.rstrip(" ,;:-") + "…"

    for line in title_lines:
        draw.text(
            (inner_x, text_y),
            line,
            font=title_font,
            fill=palette["text"],
        )
        text_y += title_line_height

    text_y += int(height * 0.022)

    # Divider.
    draw.rounded_rectangle(
        (
            inner_x,
            text_y,
            inner_x + int(width * 0.12),
            text_y + max(3, int(width * 0.004)),
        ),
        radius=3,
        fill=palette["accent2"],
    )
    text_y += int(height * 0.025)

    # Short summary in a comfortably readable font.
    footer_top = panel_bottom - int(height * 0.105)
    available_body_height = max(0, footer_top - text_y)

    body_text = _shorten(summary, 125) if summary else ""
    body_font_size = int(width * 0.029)
    body_font = _font(body_font_size)

    body_line_height = int(_text_height(draw, "Ag", body_font) * 1.28)
    max_body_lines = min(
        3,
        max(0, available_body_height // max(1, body_line_height)),
    )

    if body_text and max_body_lines > 0:
        text_y, _ = _draw_wrapped_text(
            draw,
            body_text,
            inner_x,
            text_y,
            inner_width,
            body_font,
            palette["muted"],
            max_lines=max_body_lines,
            line_spacing=1.28,
        )

    # Footer separator and source attribution.
    footer_y = panel_bottom - int(height * 0.085)

    draw.line(
        (
            inner_x,
            footer_y,
            width - pad - int(width * 0.045),
            footer_y,
        ),
        fill=palette["muted"],
        width=max(1, int(width * 0.0015)),
    )

    source = _source_label(source_url, publisher)
    footer_font = _font(int(width * 0.020), bold=True)
    date_font = _font(int(width * 0.018))

    source_max_width = int(inner_width * 0.66)
    source = _shorten(source, 42)

    while source and _text_width(draw, source, footer_font) > source_max_width:
        source = source[:-2].rstrip() + "…"

    draw.text(
        (inner_x, footer_y + int(height * 0.025)),
        source or "News source",
        font=footer_font,
        fill=palette["text"],
    )

    if published_date:
        date_text = _shorten(str(published_date), 25)
        date_width = _text_width(draw, date_text, date_font)

        if date_width <= inner_width * 0.45:
            draw.text(
                (
                    width - pad - int(width * 0.045) - date_width,
                    footer_y + int(height * 0.027),
                ),
                date_text,
                font=date_font,
                fill=palette["muted"],
            )

    # Tiny signature at the bottom of the image.
    signature_font = _font(int(width * 0.016))
    signature = "CONTEXT BEFORE CLICKS"

    draw.text(
        (
            pad,
            height - int(height * 0.035),
        ),
        signature,
        font=signature_font,
        fill=palette["muted"],
    )

    # Save at the requested location.
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    image.save(destination, format="PNG", optimize=True)

    return destination

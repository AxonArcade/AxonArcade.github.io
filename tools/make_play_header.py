"""Draws the Google Play developer page header image for Axon Arcade.

Play wants 4096 x 2304, JPEG or 24-bit PNG with no transparency. The logo and
text sit in the middle so they survive however Play crops the edges; the cards,
streaks and sparkles around them are decoration and can be cut.

    python3 tools/make_play_header.py

Writes store/play-developer-header.png and .jpg. Needs Pillow and numpy.
"""

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "assets/fonts/fredoka-latin.woff2"
OUT = ROOT / "store"

W, H = 4096, 2304
SS = 2  # supersampling for shapes drawn on their own layers

# Swipe Mania's palette (scripts/core/palette.gd) and the site's accents.
RED, BLUE, GREEN, YELLOW = "#f0434a", "#3d8bff", "#34c759", "#ffd60a"
ORANGE, PURPLE, PINK, CYAN = "#ff8a1f", "#a35cff", "#ff6ec7", "#3dd5ff"
CARD = "#232838"
MARK_FROM, MARK_TO = (107, 60, 255), (255, 79, 154)


def rgb(hex_colour):
    h = hex_colour.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def font(size, weight):
    f = ImageFont.truetype(str(FONT), size)
    f.set_variation_by_axes([weight])
    return f


def background():
    """Indigo to teal, like the game, with soft glows and a dark vignette."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    t = np.clip(0.7 * y / H + 0.3 * x / W, 0, 1)[..., None]
    top = np.array([46, 14, 128], np.float32)
    bottom = np.array([18, 70, 98], np.float32)
    img = top + (bottom - top) * t

    def glow(cx, cy, r, colour, strength):
        d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / r
        a = np.clip(1 - d, 0, 1)[..., None] ** 2 * strength
        return a * (np.array(colour, np.float32) - img)

    img += glow(W * 0.5, H * 0.47, 1500, (139, 123, 255), 0.45)
    img += glow(W * 0.9, H * 0.05, 1300, (255, 79, 154), 0.35)
    img += glow(W * 0.08, H * 1.0, 1300, (24, 120, 150), 0.40)

    # Vignette: darken towards the corners.
    d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    img *= (1 - 0.32 * np.clip(d - 0.55, 0, 1) ** 1.5)[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")


def streaks(canvas, start, end, bend, direction):
    """Four colour trails, fading out behind a flung card (from the app icon).
    [direction] is +1 for trails fading towards the left, -1 towards the right."""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    colours = [YELLOW, ORANGE, GREEN, CYAN]
    for i, c in enumerate(colours):
        off = i * 120
        (x0, y0), (x1, y1) = (start[0], start[1] + off), (end[0], end[1] + off)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 - bend
        steps = 260
        width = 52
        for s in range(steps + 1):
            u = s / steps
            px = (1 - u) ** 2 * x0 + 2 * (1 - u) * u * cx + u ** 2 * x1
            py = (1 - u) ** 2 * y0 + 2 * (1 - u) * u * cy + u ** 2 * y1
            fade = u if direction > 0 else 1 - u
            alpha = int(255 * fade ** 1.6)
            d.ellipse((px - width / 2, py - width / 2, px + width / 2, py + width / 2),
                      fill=rgb(c) + (alpha,))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1.5)))


def card(canvas, centre, size, angle, text, fill, ink="#ffffff", outline=None):
    """An in-game card: a rounded square with two darker cards stacked under it."""
    s = size * SS
    pad = int(s * 0.25)
    layer = Image.new("RGBA", (s + pad * 2, s + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r = int(s * 0.17)
    for k, shade in ((2, (40, 34, 96)), (1, (52, 44, 120))):
        inset = int(s * 0.04 * k)
        drop = int(s * 0.045 * k)
        d.rounded_rectangle((pad + inset, pad + drop, pad + s - inset, pad + s + drop - inset // 2),
                            r, fill=shade + (255,))
    d.rounded_rectangle((pad, pad, pad + s, pad + s), r, fill=rgb(fill) + (255,))

    lines = text.split("\n")
    longest = max(lines, key=len)
    fsize = int(s * min(0.30, 1.45 / max(len(longest), 1)))
    f = font(fsize, 700)
    stroke = int(fsize * 0.07) if outline else 0
    d.multiline_text((pad + s / 2, pad + s / 2), text, font=f, fill=rgb(ink) + (255,),
                     anchor="mm", align="center", spacing=int(fsize * 0.05),
                     stroke_width=stroke, stroke_fill=rgb(outline) + (255,) if outline else None)

    layer = layer.resize((layer.width // SS, layer.height // SS), Image.LANCZOS)
    layer = layer.rotate(angle, resample=Image.BICUBIC, expand=True)

    # Drop shadow.
    shadow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    shadow.putalpha(layer.getchannel("A").point(lambda a: a * 0.55))
    shadow = shadow.filter(ImageFilter.GaussianBlur(size * 0.07))
    x = int(centre[0] - layer.width / 2)
    y = int(centre[1] - layer.height / 2)
    canvas.alpha_composite(shadow, (x, y + int(size * 0.09)))
    canvas.alpha_composite(layer, (x, y))


def sparkle(canvas, centre, radius, colour, opacity=1.0):
    """A four-point sparkle with curved sides, like the ones in the app icon."""
    R = radius * SS
    layer = Image.new("RGBA", (R * 2 + 4, R * 2 + 4), (0, 0, 0, 0))
    pts = []
    for i in range(240):
        t = 2 * math.pi * i / 240
        c, s = math.cos(t), math.sin(t)
        pts.append((R + 2 + R * math.copysign(abs(c) ** 3.2, c),
                    R + 2 + R * math.copysign(abs(s) ** 3.2, s)))
    ImageDraw.Draw(layer).polygon(pts, fill=rgb(colour) + (int(255 * opacity),))
    layer = layer.resize((layer.width // SS, layer.height // SS), Image.LANCZOS)
    glow = layer.filter(ImageFilter.GaussianBlur(radius * 0.35))
    pos = (int(centre[0] - layer.width / 2), int(centre[1] - layer.height / 2))
    canvas.alpha_composite(glow, pos)
    canvas.alpha_composite(layer, pos)


def outline_shape(canvas, kind, centre, radius, colour, opacity, angle=0):
    """Faint outlined circle / square / triangle, the game's edge shapes."""
    R = radius * SS
    size = R * 2 + 40 * SS
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = size / 2
    col = rgb(colour) + (int(255 * opacity),)
    w = 13 * SS
    if kind == "circle":
        d.ellipse((c - R, c - R, c + R, c + R), outline=col, width=w)
    elif kind == "square":
        d.rounded_rectangle((c - R * 0.85, c - R * 0.85, c + R * 0.85, c + R * 0.85),
                            R * 0.18, outline=col, width=w)
    elif kind == "triangle":
        pts = [(c + R * math.cos(math.radians(a)), c + R * math.sin(math.radians(a)))
               for a in (-90, 30, 150)]
        d.line(pts + [pts[0], pts[1]], fill=col, width=w, joint="curve")
    layer = layer.resize((size // SS, size // SS), Image.LANCZOS).rotate(angle, resample=Image.BICUBIC)
    canvas.alpha_composite(layer, (int(centre[0] - layer.width / 2), int(centre[1] - layer.height / 2)))


def mark(size):
    """The Axon Arcade mark (assets/img/axon-mark.svg), drawn at [size] px."""
    s = size * SS
    k = s / 64
    # Gradient tile.
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    t = np.clip((xx + yy) / (2 * s), 0, 1)[..., None]
    grad = np.array(MARK_FROM, np.float32) + (np.array(MARK_TO, np.float32) - np.array(MARK_FROM, np.float32)) * t
    tile = Image.fromarray(grad.astype(np.uint8)).convert("RGBA")
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, s - 1, s - 1), 16 * k, fill=255)
    tile.putalpha(mask)
    d = ImageDraw.Draw(tile)
    white = (255, 255, 255, 255)
    centre = (32 * k, 34 * k)
    for end in ((17, 19), (47, 19), (32, 50)):
        d.line([centre, (end[0] * k, end[1] * k)], fill=white, width=int(5 * k))
    for cx, cy in ((17, 19), (47, 19), (32, 51)):
        d.ellipse(((cx - 5.5) * k, (cy - 5.5) * k, (cx + 5.5) * k, (cy + 5.5) * k), fill=white)
    d.ellipse(((32 - 10.5) * k, (34 - 10.5) * k, (32 + 10.5) * k, (34 + 10.5) * k), fill=white)
    d.ellipse(((32 - 7.5) * k, (34 - 7.5) * k, (32 + 7.5) * k, (34 + 7.5) * k), fill=rgb(YELLOW) + (255,))
    return tile.resize((size, size), Image.LANCZOS)


def shadowed_text(canvas, xy, text, f, fill, blur, offset, opacity):
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text((xy[0], xy[1] + offset), text, font=f, fill=(10, 6, 40, int(255 * opacity)), anchor="mm")
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(canvas).text(xy, text, font=f, fill=fill, anchor="mm")


def main():
    img = background()

    # Faint edge shapes in the background.
    outline_shape(img, "circle", (1260, 330), 70, BLUE, 0.35)
    outline_shape(img, "square", (2950, 2010), 64, PINK, 0.35, angle=12)
    outline_shape(img, "triangle", (1180, 1990), 72, CYAN, 0.35, angle=-8)
    outline_shape(img, "circle", (2860, 300), 46, YELLOW, 0.30)
    outline_shape(img, "square", (180, 1220), 50, PURPLE, 0.35, angle=-15)
    outline_shape(img, "triangle", (3930, 1180), 56, ORANGE, 0.35, angle=10)

    # Left: cards flung towards the middle, trails behind them.
    streaks(img, (-120, 1090), (560, 990), 110, +1)
    card(img, (520, 760), 560, 13, "NOT\nRED", PURPLE)
    card(img, (790, 1560), 600, -9, "LEFT", CARD)

    # Right: the mirror image.
    streaks(img, (3540, 990), (4220, 1090), 110, -1)
    card(img, (3560, 780), 600, -11, "PINK", BLUE, ink=YELLOW, outline="#111111")
    card(img, (3310, 1580), 560, 8, "GREEN", GREEN)

    # Sparkles.
    for centre, r, c, o in [((1330, 560), 70, YELLOW, 1), ((2790, 520), 52, "#ffffff", 1),
                            ((1420, 1760), 40, "#ffffff", 0.9), ((2700, 1800), 64, YELLOW, 1),
                            ((170, 1930), 40, "#ffffff", 0.8), ((3960, 330), 48, "#ffffff", 0.9),
                            ((1730, 400), 26, "#ffffff", 0.8), ((3760, 2050), 42, YELLOW, 0.9),
                            ((1040, 330), 30, "#ffffff", 0.7), ((3100, 1240), 30, "#ffffff", 0.7)]:
        sparkle(img, centre, r, c, o)

    # Centre: mark, wordmark, rainbow rule, tagline.
    m = mark(430)
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle((W / 2 - 215, 650 + 30, W / 2 + 215, 650 + 460), 110, fill=(10, 6, 40, 150))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(40)))
    img.alpha_composite(m, (int(W / 2 - m.width / 2), 650))

    word = font(270, 700)
    shadowed_text(img, (W / 2, 1290), "Axon Arcade", word, (255, 255, 255, 255), blur=22, offset=16, opacity=0.55)
    left, _, right, _ = ImageDraw.Draw(img).textbbox((W / 2, 1290), "Axon Arcade", font=word, anchor="mm")
    print(f"wordmark spans x {left:.0f}..{right:.0f}")

    rule_w, rule_h, rule_y = 420, 24, 1490
    seg = rule_w / 4
    rule = Image.new("RGBA", (rule_w * SS, rule_h * SS), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rule)
    for i, c in enumerate([YELLOW, ORANGE, GREEN, CYAN]):
        rd.rectangle((i * seg * SS, 0, (i + 1) * seg * SS, rule_h * SS), fill=rgb(c) + (255,))
    rmask = Image.new("L", rule.size, 0)
    ImageDraw.Draw(rmask).rounded_rectangle((0, 0, rule.width - 1, rule.height - 1), rule_h * SS // 2, fill=255)
    rule.putalpha(rmask)
    rule = rule.resize((rule_w, rule_h), Image.LANCZOS)
    img.alpha_composite(rule, (int(W / 2 - rule_w / 2), rule_y))

    tag = font(112, 500)
    shadowed_text(img, (W / 2, 1640), "Short, fast games for your phone", tag, rgb(YELLOW) + (255,),
                  blur=14, offset=8, opacity=0.5)

    OUT.mkdir(exist_ok=True)
    final = img.convert("RGB")
    final.save(OUT / "play-developer-header.png", optimize=True)
    final.save(OUT / "play-developer-header.jpg", quality=90, optimize=True, progressive=True)
    print("wrote", OUT / "play-developer-header.png")


if __name__ == "__main__":
    main()

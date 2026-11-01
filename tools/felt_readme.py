#!/usr/bin/env python3
"""Felt artwork for the README: the Counterfoil wordmark, section headers, the results band and the crew cards.

Pillow only. Fonts: Arial Rounded MT Bold (the site's --cf-display fallback) and Arial. Everything is rendered
at 2x and placed in the README at half size. Colours are the dashboard's second palette (globals.css --dw-*).

    python3 tools/felt_readme.py            # writes docs/brand/readme/
"""
from __future__ import annotations

import math
import os
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "brand", "readme")
CREW = os.path.join(ROOT, "dashboard", "public", "crew")
ROUNDED = "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"
PLAIN = "/System/Library/Fonts/Supplemental/Arial.ttf"
S = 2  # render scale

PAL = {
    "espresso": (45, 30, 25), "espresso2": (58, 39, 33), "ink": (28, 18, 16),
    "cream": (251, 247, 242), "wool": (244, 236, 223),
    "lilac": (228, 161, 245), "butter": (246, 217, 138), "orange": (233, 138, 58), "powder": (197, 208, 230),
    "plum": (109, 31, 94),
}


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


# ---------- felt primitives ----------

def felt_fill(size: tuple[int, int], color: tuple[int, int, int], seed: int = 7) -> Image.Image:
    """A flat colour with wool fibre: fine noise plus a coarse mottling, both multiplied in."""
    w, h = size
    fine = Image.effect_noise((w, h), 46).filter(ImageFilter.GaussianBlur(0.9))
    coarse = Image.effect_noise((max(1, w // 8), max(1, h // 8)), 70).resize((w, h), Image.BILINEAR).filter(ImageFilter.GaussianBlur(4))
    # multiply factors a little under 1.0; the base is brightened first so the average stays the colour asked for.
    # Light colours can't be brightened, so they get a gentler fibre, or cream turns grey.
    lum = sum(color) / 3
    gain, c1, k1, c2, k2 = (1.07, 232, 0.36, 242, 0.22) if lum < 200 else (1.0, 249, 0.14, 252, 0.08)
    base = Image.new("RGB", size, tuple(min(255, int(c * gain)) for c in color))
    f1 = fine.point(lambda v: max(0, min(255, int(c1 + (v - 128) * k1))))
    f2 = coarse.point(lambda v: max(0, min(255, int(c2 + (v - 128) * k2))))
    out = ImageChops.multiply(base, Image.merge("RGB", (f1, f1, f1)))
    out = ImageChops.multiply(out, Image.merge("RGB", (f2, f2, f2)))
    return out


def fuzzy(mask: Image.Image, fuzz: float) -> Image.Image:
    """Roughen a mask's edge the way cut felt frays: blur, add noise, threshold, soften."""
    soft = mask.filter(ImageFilter.GaussianBlur(fuzz))
    n = Image.effect_noise(mask.size, 64).filter(ImageFilter.GaussianBlur(1.1))
    up = n.point(lambda v: max(0, int((v - 128) * 0.5)))
    down = n.point(lambda v: max(0, int((128 - v) * 0.5)))
    comb = ImageChops.subtract(ImageChops.add(soft, up), down)
    return comb.point(lambda v: 255 if v > 128 else 0).filter(ImageFilter.GaussianBlur(0.7))


def rounded_rect_mask(size: tuple[int, int], box: tuple[int, int, int, int], r: int) -> Image.Image:
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=r, fill=255)
    return m


def rounded_path(x0: float, y0: float, x1: float, y1: float, r: float, step: float = 2.0) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []

    def arc(cx: float, cy: float, a0: float, a1: float) -> None:
        n = max(6, int(abs(a1 - a0) / 3))
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))

    def line(ax: float, ay: float, bx: float, by: float) -> None:
        n = max(1, int(math.hypot(bx - ax, by - ay) / step))
        for i in range(n + 1):
            pts.append((ax + (bx - ax) * i / n, ay + (by - ay) * i / n))

    line(x0 + r, y0, x1 - r, y0); arc(x1 - r, y0 + r, -90, 0)
    line(x1, y0 + r, x1, y1 - r); arc(x1 - r, y1 - r, 0, 90)
    line(x1 - r, y1, x0 + r, y1); arc(x0 + r, y1 - r, 90, 180)
    line(x0, y1 - r, x0, y0 + r); arc(x0 + r, y0 + r, 180, 270)
    return pts


def stitch(layer: Image.Image, pts: list[tuple[float, float]], color: tuple[int, int, int], width: int, on: float, off: float) -> None:
    """Dashed running stitch along a path, round-capped, with a soft shadow under each stitch."""
    shadow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    thread = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ds, dt = ImageDraw.Draw(shadow), ImageDraw.Draw(thread)
    dist = 0.0
    seg: list[tuple[float, float]] = []
    drawing = True
    phase = 0.0
    for i in range(1, len(pts)):
        a, b = pts[i - 1], pts[i]
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        if drawing:
            seg.append(a)
        phase += d
        limit = on if drawing else off
        if phase >= limit:
            if drawing:
                seg.append(b)
                for canvas, col, dy in ((ds, (0, 0, 0, 70), 3), (dt, color + (255,), 0)):
                    moved = [(x, y + dy) for x, y in seg]
                    canvas.line(moved, fill=col, width=width, joint="curve")
                    for x, y in (moved[0], moved[-1]):
                        canvas.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=col)
                seg = []
            drawing = not drawing
            phase = 0.0
        dist += d
    shadow = shadow.filter(ImageFilter.GaussianBlur(2))
    layer.alpha_composite(shadow)
    layer.alpha_composite(thread)


def patch(size: tuple[int, int], color: tuple[int, int, int], thread: tuple[int, int, int], radius: int,
          inset: int = 18, fuzz: float = 2.2, shadow: bool = True) -> Image.Image:
    """A cut felt patch with a running stitch inside its edge, on a transparent canvas with room for the shadow."""
    w, h = size
    pad = 24
    cw, ch = w + 2 * pad, h + 2 * pad
    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    box = (pad, pad, pad + w, pad + h)
    mask = fuzzy(rounded_rect_mask((cw, ch), box, radius), fuzz)
    if shadow:
        sh = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        sh.putalpha(mask.point(lambda v: int(v * 0.28)))
        sh = sh.filter(ImageFilter.GaussianBlur(9))
        sh = ImageChops.offset(sh, 0, 6)
        canvas.alpha_composite(sh)
    body = felt_fill((cw, ch), color).convert("RGBA")
    body.putalpha(mask)
    canvas.alpha_composite(body)
    pts = rounded_path(box[0] + inset, box[1] + inset, box[2] - inset, box[3] - inset, max(4, radius - inset))
    stitch(canvas, pts, thread, width=5, on=16, off=11)
    return canvas


def felt_text(text: str, fnt: ImageFont.FreeTypeFont, color: tuple[int, int, int], fuzz: float = 1.0) -> Image.Image:
    """Text cut from felt: frayed edge, fibre fill, a soft drop shadow."""
    bbox = fnt.getbbox(text)
    pad = 16
    w, h = bbox[2] - bbox[0] + 2 * pad, bbox[3] - bbox[1] + 2 * pad
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text((pad - bbox[0], pad - bbox[1]), text, font=fnt, fill=255)
    m = fuzzy(m, fuzz)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh.putalpha(m.point(lambda v: int(v * 0.35)))
    out.alpha_composite(ImageChops.offset(sh.filter(ImageFilter.GaussianBlur(3)), 0, 3))
    body = felt_fill((w, h), color).convert("RGBA")
    body.putalpha(m)
    out.alpha_composite(body)
    return out


def paste_center(canvas: Image.Image, img: Image.Image, cx: float, cy: float) -> None:
    canvas.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))


def save(img: Image.Image, name: str, quality: int = 90) -> None:
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    if name.endswith(".webp"):
        img.save(path, "WEBP", quality=quality, method=6)
    else:
        img.save(path, "PNG", optimize=True)
    print(f"{os.path.getsize(path) // 1024:5d} KB  {name}  {img.size[0]}x{img.size[1]}")


# ---------- pieces ----------

def header(slug: str, text: str, color: str, ink: str, thread: str) -> None:
    fnt = font(ROUNDED, 68 * S // 2)  # 68 px at 2x → 34 px on the page
    t = felt_text(text, fnt, PAL[ink])
    w, h = t.width + 44 * S, 68 * S
    p = patch((w, h), PAL[color], PAL[thread], radius=22 * S, inset=9 * S)
    paste_center(p, t, p.width / 2, p.height / 2 - 2)
    save(p, f"h-{slug}.png")


def wordmark() -> None:
    fnt = font(ROUNDED, 150 * S // 2 * 2)
    t = felt_text("Counterfoil", fnt, PAL["cream"], fuzz=1.6)
    w, h = t.width + 70 * S, t.height + 26 * S
    p = patch((w, h), PAL["espresso"], PAL["lilac"], radius=34 * S, inset=12 * S)
    paste_center(p, t, p.width / 2, p.height / 2 - 4)
    save(p, "wordmark.png")


def band() -> None:
    blocks = [
        ("0", "/270", ["attack runs where wrong", "money moved, with Counterfoil"], "espresso", "cream", "cream"),
        ("99", "/270", ["the same attacks", "with no gate"], "orange", "espresso", "espresso"),
        ("82%", "", ["genuine requests", "still handled right"], "lilac", "espresso", "espresso"),
        ("9", "", ["AI models tested,", "local and cloud"], "powder", "espresso", "espresso"),
    ]
    bw, bh, gap = 300 * S, 230 * S, 8 * S
    canvas = Image.new("RGBA", (4 * bw + 3 * gap + 48, bh + 60), (0, 0, 0, 0))
    big, small, cap = font(ROUNDED, 76 * S), font(ROUNDED, 30 * S), font(PLAIN, 16 * S)
    for i, (num, den, lines, color, ink, thread) in enumerate(blocks):
        p = patch((bw, bh), PAL[color], PAL[thread], radius=20 * S, inset=9 * S)
        x = 24 + i * (bw + gap) - 24
        d = ImageDraw.Draw(p)
        n = felt_text(num, big, PAL[ink], fuzz=1.2)
        p.alpha_composite(n, (26 * S, 30 * S))
        if den:
            dn = felt_text(den, small, PAL[ink], fuzz=0.8)
            p.alpha_composite(dn, (26 * S + n.width - 12 * S, 30 * S + n.height - dn.height - 6 * S))
        for j, line in enumerate(lines):
            d.text((28 * S, 160 * S + j * 24 * S), line, font=cap, fill=PAL[ink])
        canvas.alpha_composite(p, (x, 0))
    save(canvas, "band.webp", quality=92)


def crew_card(slug: str, name: str, role: str, portrait: str, color: str, ink: str, portrait_h: int = 232) -> None:
    cw, ch = 300 * S, 380 * S
    card = patch((cw, ch), PAL["wool"], PAL["espresso"], radius=26 * S, inset=10 * S)
    img = Image.open(os.path.join(CREW, portrait)).convert("RGBA")
    scale = min((cw - 60 * S) / img.width, portrait_h * S / img.height)
    img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    # a soft shadow on the felt under the figure
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((card.width / 2 - img.width * 0.36, 24 + 258 * S, card.width / 2 + img.width * 0.36, 24 + 272 * S), fill=(45, 30, 25, 60))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    card.alpha_composite(img, (int(card.width / 2 - img.width / 2), int(24 + 268 * S - img.height)))
    size = 30 * S
    while True:  # long names shrink until the tag fits inside the card
        nm = felt_text(name, font(ROUNDED, size), PAL[ink], fuzz=0.9)
        if nm.width + 30 * S <= cw - 56 * S or size <= 18 * S:
            break
        size -= 2
    tag = patch((nm.width + 30 * S, 46 * S), PAL[color], PAL[ink], radius=14 * S, inset=6 * S, fuzz=1.6)
    paste_center(tag, nm, tag.width / 2, tag.height / 2 - 1)
    paste_center(card, tag, card.width / 2, 24 + 304 * S)
    d = ImageDraw.Draw(card)
    rf = font(PLAIN, 15 * S)
    tw = d.textlength(role, font=rf)
    d.text((card.width / 2 - tw / 2, 24 + 340 * S), role, font=rf, fill=PAL["espresso"])
    save(card, f"crew-{slug}.webp", quality=90)


def main() -> None:
    wordmark()
    for slug, text, color, ink, thread in [
        ("crew", "The return crew", "lilac", "espresso", "espresso"),
        ("story", "The story, in seven steps", "butter", "espresso", "espresso"),
        ("how", "How it works", "powder", "espresso", "espresso"),
        ("why", "Why PayPal and Braintree", "espresso", "cream", "lilac"),
        ("real", "What ran on a real rail", "wool", "espresso", "espresso"),
        ("show", "What these results show, and what they don't", "wool", "espresso", "espresso"),
        ("cost", "The cost of the alternatives", "orange", "espresso", "espresso"),
        ("results", "Results", "espresso", "cream", "butter"),
        ("quickstart", "Quick start", "butter", "espresso", "espresso"),
        ("mcp", "Use it from any MCP client", "lilac", "espresso", "espresso"),
        ("architecture", "Architecture", "powder", "espresso", "espresso"),
        ("tools", "Tools used", "wool", "espresso", "espresso"),
        ("license", "License", "wool", "espresso", "espresso"),
    ]:
        header(slug, text, color, ink, thread)
    band()
    for slug, name, role, portrait, color, ink in [
        ("nella", "Nella", "the customer · not always honest", "nella-p6-v1.webp", "powder", "espresso"),
        ("reader", "Reader", "AI agent · reads the note", "reader-wave-v1.webp", "orange", "espresso"),
        ("runner", "Runner", "AI agent · prepares the action", "runner-wave-v1.webp", "powder", "espresso"),
        ("counterfoil", "Counterfoil", "transaction gate · checks the rules", "counterfoil-meshy.webp", "lilac", "espresso"),
        ("manager", "Store manager", "human decision · reviews held calls", "manager-wave-v1.webp", "butter", "espresso"),
        ("paypal", "PayPal / Braintree", "payment rail · moves the money", "paypal-wave-v1.webp", "espresso", "cream"),
    ]:
        crew_card(slug, name, role, portrait, color, ink)


if __name__ == "__main__":
    main()

"""The curly wool fibre tile of the 3D Counterfoil as a PNG, for Blender (tools/counterfoil_claude_3d.py).
Same seeded strokes as fibres() in dashboard/app/counterfoil-3d.tsx, so the render and the page wear the same felt.
Drawn at 2x and scaled down for smooth strokes.
Run: python3 tools/felt_fibre_tile.py  -> docs/gorseller/karakterler/felt-fibre-tile.png
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/gorseller/karakterler/felt-fibre-tile.png'
N, S = 512, 2

seed = 7


def rnd():
    global seed
    seed = (seed * 16807) % 2147483647
    return seed / 2147483647


img = Image.new('RGBA', (N * S, N * S), (128, 128, 128, 255))
g = ImageDraw.Draw(img, 'RGBA')
for _ in range(1500):
    pts = []
    x, y, a = rnd() * N, rnd() * N, rnd() * math.pi * 2
    curl, steps = (rnd() - 0.5) * 0.5, 8 + math.floor(rnd() * 22)
    for _k in range(steps):
        pts.append((x, y))
        a += curl + (rnd() - 0.5) * 0.35
        x += math.cos(a) * 4.5
        y += math.sin(a) * 4.5
    light = rnd() < 0.55
    alpha = int(255 * ((0.16 + rnd() * 0.2) if light else (0.14 + rnd() * 0.18)))
    colour = (255, 255, 255, alpha) if light else (0, 0, 0, alpha)
    width = max(1, round((1.6 + rnd() * 2.2) * S))
    for ox in (-N, 0, N):
        for oy in (-N, 0, N):
            g.line([((px + ox) * S, (py + oy) * S) for px, py in pts], fill=colour, width=width, joint='curve')
img.convert('L').resize((N, N), Image.LANCZOS).save(OUT)
print('[FIBRES]', OUT)

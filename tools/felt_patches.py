"""Codex's model-name felt patches (docs/gorseller/site-tasarim/model-patches-v1/) -> dashboard/public/models/*.webp.

Soft shadow pixels under the alpha threshold are dropped, the patch is cropped to what is left and scaled to 96 px high
(the pill shows it at 48 px). `<slug>-selected.png` becomes `<slug>-on.webp`.
"""
import pathlib
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / 'docs/gorseller/site-tasarim/model-patches-v1'
OUT = ROOT / 'dashboard/public/models'
HEIGHT = 96

OUT.mkdir(parents=True, exist_ok=True)
for png in sorted(SRC.glob('*.png')):
    im = Image.open(png).convert('RGBA')
    a = im.getchannel('A').point(lambda v: 0 if v < 24 else v)
    im.putalpha(a)
    im = im.crop(a.getbbox())
    im = im.resize((round(im.width * HEIGHT / im.height), HEIGHT), Image.LANCZOS)
    name = png.stem.replace('-normal', '').replace('-selected', '-on')
    im.save(OUT / f'{name}.webp', 'WEBP', quality=88, method=6)
    print(name, im.size, file=sys.stderr)

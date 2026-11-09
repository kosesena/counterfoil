"""The HOMI store: a homeware shop with a checkout counter, as one diorama, plus its jointed cast.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python tools/build_homi_store.py

Writes demo/static/world/homi-store.glb. The figures are empties with knee and elbow joints; the page animates them.
Blender +X/+Y/+Z is three.js +X/-Z/+Y. A figure faces -Y, the open front of the store.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from homi_kit import *  # noqa: F401,F403
from homi_kit import M, mat, make_coll, link, empty, box, rounded_slab, cyl, sphere, capsule, capsule_between, torus, text_mesh, groove_material, face_plane, finish_mesh
import homi_kit

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORLD = os.path.join(REPO, "demo", "static", "world")
scene = homi_kit.scene
random.seed(11)

M.update({
    "gateled": mat("SE_GateLED", "#ffd9a8", 0.3, emit="#ffc27a", emit_strength=2.2),
    "plaster": mat("M_Plaster", "#efe3cf", 0.92), "sage_wall": mat("M_SageWall", "#869b80", 0.85),
    "terracotta": mat("M_Terracotta", "#c8704a", 0.75), "linen_blue": mat("M_LinenBlue", "#7f9bb3", 0.9),
    "ochre": mat("M_Ochre", "#d9a441", 0.85), "blush": mat("M_Blush", "#e3b2a0", 0.9), "forest": mat("M_Forest", "#3f6650", 0.85),
    "ceramic": mat("M_Ceramic", "#f2ebdd", 0.32), "ceramic_b": mat("M_CeramicBlue", "#4d6f8c", 0.3), "ceramic_t": mat("M_CeramicTerra", "#c47a55", 0.34),
    "wax": mat("M_Wax", "#f4ead2", 0.5), "flame": mat("M_Flame", "#ffcf87", 0.3, emit="#ffb65c", emit_strength=5.0),
    "blush_glow": mat("M_RobotBlush", "#ff9d8d", 0.4, emit="#ff8a78", emit_strength=0.8),
    "enamel_ochre": mat("M_EnamelOchre", "#dfa63c", 0.28), "enamel_sage": mat("M_EnamelSage", "#8fab8c", 0.28), "enamel_ivory": mat("M_EnamelIvory", "#efe7d8", 0.3),
    "halo": mat("M_AgentHalo", "#a6ecff", 0.3, emit="#5fd8ff", emit_strength=4.5), "visor": mat("M_AgentVisor", "#9ee8ff", 0.2, emit="#49ccff", emit_strength=3.4),
    "brand": mat("M_HomiNavy", "#21365c", 0.5), "sky": mat("M_WindowSky", "#dcecf7", 0.5, emit="#e6f2fb", emit_strength=1.25), "skyline": mat("M_Skyline", "#bcd0df", 0.6, emit="#c9dae6", emit_strength=0.75), "skyline2": mat("M_Skyline2", "#a5bdcf", 0.6, emit="#b4c9d9", emit_strength=0.7), "frame": mat("M_WindowFrame", "#21365c", 0.5), "sign": mat("M_SignGlow", "#fff0d6", 0.3, emit="#ffd9a0", emit_strength=3.2),
    "brand_screen": mat("M_ScreenNavy", "#142238", 0.3, emit="#1d3a66", emit_strength=0.9), "brass_m": mat("M_Brass", "#c9a35f", 0.28, metal=0.85),
    "tile": mat("M_TileEntry", "#e8ddca", 0.5), "rubber": mat("M_Rubber", "#2c2d30", 0.6), "esc_step": mat("M_EscStep", "#7c8087", 0.4, metal=0.5),
    "acrylic": mat("SE_GateAcrylic", "#e6f2f6", 0.05, alpha=0.3), "glass_b": mat("M_OfficeGlass", "#dcebf0", 0.05, alpha=0.1),
})
# daylight palette: birch, white, HOMI navy, coral
M.update({
    "walnut": mat("M_Birch", "#dcc8a6", 0.5), "dark_wood": mat("M_BirchDark", "#bfa67f", 0.55), "dark_cabinet": mat("M_CounterNavy", "#21365c", 0.45),
    "offwhite": mat("M_ShelfWhite", "#f3efe7", 0.7), "plaster": mat("M_WallWhite", "#f7f4ee", 0.9), "platform": mat("M_PlinthGrey", "#dcd8d0", 0.8),
    "rattan": mat("M_OpalGlobe", "#fffaf0", 0.25, emit="#fff4df", emit_strength=1.5), "led_2700": mat("M_LedNeutral", "#fff6e6", 0.3, emit="#fff0d6", emit_strength=3.0),
    "led_2700_soft": mat("M_LedNeutralSoft", "#fff6e6", 0.3, emit="#fff0d6", emit_strength=1.3), "cognac": mat("M_Coral", "#e26d55", 0.5), "rust": mat("M_CoralDeep", "#d9604a", 0.75),
    "sign": mat("M_SignWhite", "#ffffff", 0.3, emit="#ffffff", emit_strength=1.6), "light_oak": mat("M_TopWhite", "#f2eee6", 0.35), "kraft": mat("M_BoxSand", "#d8c4a2", 0.8),
})
W, D, H = 15.7, 9.7, 3.0        # room
XW, YB = W / 2, D / 2           # side walls at +-XW, back wall at +YB
CY, CH, CD = 2.7, 1.02, 0.78    # counter centre line, height, depth
env = make_coll("Store")
b = lambda n, s, l, m, bevel=0.012, **k: box(n, env, s, l, M[m] if isinstance(m, str) else m, bevel=bevel, **k)
c = lambda n, r, d, l, m, **k: cyl(n, env, r, d, l, M[m] if isinstance(m, str) else m, **k)
s = lambda n, r, l, m, **k: sphere(n, env, r, l, M[m] if isinstance(m, str) else m, **k)
LIGHTS = []

# ------------------------------------------------------------------ shell
rounded_slab("Platform", env, W + 0.3, D + 0.3, 0.32, 0.3, (0, 0, -0.16), M["platform"])
import numpy as np
from homi_kit import np_image, tex_material, hex_srgb
rng = np.random.default_rng(5); N = 1024
img = np.tile(np.array(hex_srgb("#ece8df")), (N, N, 1)).astype(np.float32)
base = img[0, 0].copy()
chips = [np.array(hex_srgb(h), dtype=np.float32) * 0.55 + base * 0.45 for h in ("#21365c", "#e26d55", "#8fab8c", "#bdb6a8", "#ffffff", "#d8c4a2")]
for _ in range(5200):  # small soft stones, irregular rather than square
    x0, y0_, r_ = int(rng.integers(N)), int(rng.integers(N)), float(rng.uniform(1.6, 5.2)); col = chips[int(rng.integers(len(chips)))]
    ax, ay = rng.uniform(0.7, 1.3), rng.uniform(0.7, 1.3); R_ = int(r_ * 1.4) + 1
    for yy in range(-R_, R_ + 1):
        for xx in range(-R_, R_ + 1):
            if (xx / ax) ** 2 + (yy / ay) ** 2 <= r_ * r_: img[(y0_ + yy) % N, (x0 + xx) % N] = col
oak = tex_material("M_FloorTerrazzo", np_image("terrazzo_img", img), 0.3)
floor = rounded_slab("Floor", env, W, D, 0.006, 0.18, (0, 0, 0.0005), oak, edge_bevel=0.002)
uv = floor.data.uv_layers.new(name="UVMap")
for lp in floor.data.loops:
    co = floor.data.vertices[lp.vertex_index].co; uv.data[lp.index].uv = (co.x / 2.8, co.y / 2.8)
b("EntryMat", (2.4, 3.0, 0.012), (-6.5, -2.7, 0.006), "brand", bevel=0.003)
b("WallBack", (W + 0.3, 0.2, H), (0, YB + 0.1, H / 2), "plaster")
for sx, nm in ((-1, "L"), (1, "R")):
    b(f"Wall{nm}Lo", (0.2, D, H), (sx * (XW + 0.1), 0, H / 2), "plaster")
    b(f"Cap{nm}", (0.26, D + 0.3, 0.08), (sx * (XW + 0.1), 0, H + 0.04), "walnut")
b("CapBack", (W + 0.5, 0.26, 0.08), (0, YB + 0.1, H + 0.04), "walnut")
# wainscot on all walls
wg = M["brand"]; wa = groove_material("M_Wains", "#e6e1d7", 0.86)
for nm, w_, loc, rz in (("BackL", 4.3, (-5.6, YB - 0.005, 0.6), 0), ("BackR", 2.8, (6.4, YB - 0.005, 0.6), 0)):
    face_plane(f"Wains{nm}", env, w_, 1.2, loc, wa)
# left wall: fluted sage below, posters above
fp = face_plane("WainsLeft", env, 5.6, 1.2, (0, 0, 0), wa); fp.rotation_euler = (0, 0, math.radians(-90)); fp.location = (-XW + 0.006, 1.9, 0.6)
b("WainsCapL", (0.04, 5.6, 0.04), (-XW + 0.02, 1.9, 1.22), "walnut", bevel=0.004)
b("WainsCapB", (4.3, 0.04, 0.04), (-5.6, YB - 0.02, 1.22), "walnut", bevel=0.004)
for i, (y, m, t_) in enumerate(((0.2, "teal", "SLOW"), (1.55, "mustard", "HOME"), (2.9, "rust", "MADE"))):
    b(f"Poster{i}", (0.03, 0.82, 1.08), (-XW + 0.018, y, 2.0), "walnut", bevel=0.004)
    b(f"PosterF{i}", (0.01, 0.72, 0.98), (-XW + 0.036, y, 2.0), m, bevel=0.0)
    tx = text_mesh(f"PosterT{i}", env, t_, 0.2, M["cream"], (-XW + 0.044, y, 2.0), rot=(90, 0, 90), max_w=0.58)
# ------------------------------------------------------------------ products
def mug(n, x, y, z, m="ceramic"):
    c(n, 0.05, 0.1, (x, y, z + 0.05), m, segs=14); torus(n + "H", env, 0.03, 0.009, (x + 0.06, y, z + 0.05), M[m], rot=(90, 0, 0))
def bowls(n, x, y, z, m, k=4):
    for i in range(k): c(f"{n}{i}", 0.11, 0.035, (x, y, z + 0.018 + i * 0.03), m, segs=18, r2=0.07)
def vase(n, x, y, z, m, h=0.3):
    sphere(n, env, 0.09, (x, y, z + h * 0.42), M[m], scale=(1, 1, h / 0.2), segs=16, rings=10); c(n + "N", 0.035, h * 0.3, (x, y, z + h * 0.92), m, segs=12)
def candle(n, x, y, z):
    c(n, 0.04, 0.13, (x, y, z + 0.065), "wax", segs=12); s(n + "F", 0.014, (x, y, z + 0.15), "flame", scale=(1, 1, 1.8), segs=8, rings=6)
def cushion(n, x, y, z, m, rz=0):
    sphere(n, env, 0.2, (x, y, z + 0.09), M[m], scale=(1, 1, 0.42), segs=16, rings=10)
def throw(n, x, y, z, m, w=0.46):
    for i in range(3): b(f"{n}{i}", (w, 0.3, 0.06), (x, y, z + 0.03 + i * 0.058), m, bevel=0.026)
def plant(n, x, y, h=1.1, pot="terracotta"):
    c(n + "P", 0.2, 0.34, (x, y, 0.17), pot, segs=18, r2=0.15); c(n + "T", 0.022, h, (x, y, h / 2 + 0.3), "dark_wood", segs=8)
    for i, (dz, r) in enumerate(((0.62, 0.3), (0.95, 0.26), (1.22, 0.18))):
        s(f"{n}L{i}", r * (h / 1.1), (x + 0.02 * (-1) ** i, y, 0.3 + dz * h), "leaf" if i % 2 else "leaf_light", segs=14, rings=10)
def goods(n, x, y, z, w):
    """Fills a shelf run with a mix of homeware."""
    u = -w / 2 + 0.14; i = 0
    while u < w / 2 - 0.12:
        k = random.randrange(6); t = f"{n}_{i}"; px = x + u
        if k == 0: mug(t, px, y, z, random.choice(("ceramic", "ceramic_b", "ceramic_t"))); u += 0.2
        elif k == 1: bowls(t, px, y, z, random.choice(("ceramic", "ceramic_t", "ceramic_b")), 3); u += 0.3
        elif k == 2: vase(t, px, y, z, random.choice(("ceramic_b", "ceramic_t", "forest", "ceramic")), 0.3); u += 0.27
        elif k == 3: candle(t, px, y, z); u += 0.14
        elif k == 4: throw(t, px + 0.08, y, z, random.choice(("rust", "ochre", "linen_blue", "blush", "forest")), 0.34); u += 0.46
        else: b(t, (0.2, 0.2, 0.26), (px, y, z + 0.13), random.choice(("kraft", "cream", "navy")), bevel=0.01); u += 0.27
        i += 1
def bay(n, x, w, levels=(0.55, 1.0, 1.45, 1.9), top=2.35):
    """Lit walnut shelving against the back wall."""
    y = YB - 0.2
    b(n + "Back", (w, 0.03, top), (x, YB - 0.03, top / 2), "offwhite", bevel=0.0)
    for sx in (-1, 1): b(n + f"Post{sx}", (0.07, 0.4, top), (x + sx * w / 2, y, top / 2), "walnut")
    b(n + "Base", (w, 0.42, 0.42), (x, y, 0.21), "dark_wood"); b(n + "Top", (w + 0.1, 0.44, 0.07), (x, y, top), "walnut")
    for i, z in enumerate(levels):
        b(f"{n}S{i}", (w - 0.04, 0.38, 0.035), (x, y, z), "walnut", bevel=0.004)
        b(f"{n}Led{i}", (w - 0.12, 0.012, 0.012), (x, y - 0.14, z + 0.4), "led_2700_soft", bevel=0.0)
        goods(f"{n}G{i}", x, y - 0.02, z + 0.018, w - 0.1)
    LIGHTS.append((n, (x, y - 0.5, 1.6), 22))
bay("BayL", -3.1, 2.3, levels=(0.55, 1.0), top=1.42); bay("BayR", 3.1, 2.3, levels=(0.55, 1.0), top=1.42)
# shop windows along the back wall, above the low shelving
def window(n, x0, x1, z0=1.52, z1=2.88):
    w_, xc, h_, zc = x1 - x0, (x0 + x1) / 2, z1 - z0, (z0 + z1) / 2
    face_plane(n + "Sky", env, w_, h_, (xc, YB - 0.012, zc), M["sky"])
    random.seed(int(abs(x0) * 10)); u = x0 + 0.1
    while u < x1 - 0.15:
        bw, bh = random.uniform(0.28, 0.6), random.uniform(0.3, 0.95); bw = min(bw, x1 - u - 0.02)
        b(f"{n}B{u:.2f}", (bw, 0.006, bh), (u + bw / 2, YB - 0.017, z0 + bh / 2), random.choice(("skyline", "skyline2")), bevel=0.0); u += bw + random.uniform(0.0, 0.1)
    for z_ in (z0, z1): b(f"{n}F{z_}", (w_ + 0.1, 0.05, 0.05), (xc, YB - 0.03, z_), "frame", bevel=0.0)
    k_ = max(2, round(w_ / 0.85))
    for i in range(k_ + 1): b(f"{n}M{i}", (0.05, 0.05, h_), (x0 + w_ * i / k_, YB - 0.03, zc), "frame", bevel=0.0)
window("WinL", -4.75, -1.95); window("WinR", 1.95, 4.95)
# feature wall and sign behind the counter
face_plane("FeatureWall", env, 3.7, H, (0, YB - 0.008, H / 2), wg)
b("SignPanel", (3.0, 0.08, 0.9), (0, YB - 0.06, 2.1), "brand", bevel=0.03)
text_mesh("SignHOMI", env, "HOMI", 0.72, M["sign"], (0, YB - 0.105, 2.13), max_w=2.3, extrude=0.012)
text_mesh("SignSub", env, "HOME GOODS · EST. 2026", 0.11, M["cream"], (0, YB - 0.105, 1.78), max_w=2.1)
b("SignHalo", (3.12, 0.012, 0.016), (0, YB - 0.1, 1.64), "led_2700", bevel=0.0)
LIGHTS.append(("Sign", (0, YB - 0.7, 2.1), 30))
# ------------------------------------------------------------------ checkout counter
CW = 8.2; ct = M["counter_top"]
b("CounterBody", (CW, CD - 0.08, CH - 0.05), (0, CY, (CH - 0.05) / 2), "dark_cabinet", bevel=0.02)
pnl = face_plane("CounterFlutes", env, CW - 0.04, CH - 0.16, (0, CY - CD / 2 + 0.03, 0.54), wg)
b("CounterTop", (CW + 0.16, CD + 0.08, 0.05), (0, CY, CH - 0.02), "cream", bevel=0.012)
b("CounterLed", (CW - 0.1, 0.014, 0.014), (0, CY - CD / 2 + 0.012, 0.07), "led_2700", bevel=0.0)
c("BadgeDisc", 0.34, 0.03, (-1.3, CY - CD / 2 + 0.01, 0.56), "brand", rot=(90, 0, 0), segs=40)
torus("BadgeRing", env, 0.31, 0.012, (-1.3, CY - CD / 2 - 0.005, 0.56), M["brass_m"])
text_mesh("BadgeText", env, "HOMI", 0.2, M["cream"], (-1.3, CY - CD / 2 - 0.009, 0.56), max_w=0.46)
TOP = CH + 0.005
def till(n, x):
    """Screen on a stem, card reader and a bag of receipts."""
    b(n + "Base", (0.34, 0.3, 0.06), (x, CY + 0.02, TOP + 0.03), "graphite", bevel=0.02)
    c(n + "Stem", 0.022, 0.25, (x, CY + 0.06, TOP + 0.17), "steel", segs=10)
    b(n + "Screen", (0.42, 0.03, 0.3), (x, CY + 0.04, TOP + 0.44), "graphite", bevel=0.012, rot=(-10, 0, 0))
    b(n + "Face", (0.37, 0.004, 0.25), (x, CY + 0.024, TOP + 0.44), "screen", bevel=0.0, rot=(-10, 0, 0))
    b(n + "Reader", (0.1, 0.17, 0.03), (x + 0.33, CY - 0.1, TOP + 0.015), "graphite", bevel=0.01, rot=(20, 0, 0))
till("TillReturns", -3.25); till("TillSale", -1.05)
for x, t_ in ((-2.6, "RETURNS"), (-0.4, "CHECKOUT")):
    b(f"Hang{t_}", (1.25, 0.03, 0.36), (x, CY + 0.02, 2.42), "brand", bevel=0.012)
    text_mesh(f"HangT{t_}", env, t_, 0.15, M["sign"], (x, CY - 0.002, 2.42), max_w=1.05)
    for sx in (-1, 1): c(f"Hang{t_}{sx}", 0.006, 0.42, (x + sx * 0.5, CY + 0.02, 2.82), "black_metal", segs=6)
for i, (x, m) in enumerate(((-2.05, "kraft"), (-1.75, "cream"), (-1.9, "kraft"))):
    b(f"RetBox{i}", (0.3, 0.3, 0.24), (x, CY + 0.05, TOP + 0.12 + (0.25 if i == 2 else 0)), m, bevel=0.01)
for i in range(5): b(f"BagStack{i}", (0.34, 0.24, 0.02), (3.85, CY - 0.05, TOP + 0.012 + i * 0.022), "kraft", bevel=0.002)
# pendant rail above the counter
b("RailBar", (8.4, 0.05, 0.05), (0, CY + 0.02, 2.82), "black_metal")
for sx in (-1, 1): b(f"RailArm{sx}", (0.05, YB - CY, 0.05), (sx * 3.9, (YB + CY) / 2, 2.82), "black_metal")
for i, x in enumerate((-3.9, -1.6, 2.2, 4.0)):
    if abs(x + 0.4) < 0.3: continue
    c(f"PendW{i}", 0.005, 0.42, (x, CY + 0.02, 2.6), "black_metal", segs=6)
    sphere(f"PendS{i}", env, 0.15, (x, CY + 0.02, 2.2), M["rattan"], segs=24, rings=16)
    c(f"PendC{i}", 0.03, 0.05, (x, CY + 0.02, 2.37), "brass_m", segs=12); LIGHTS.append((f"Pend{i}", (x, CY - 0.15, 1.9), 26))
# ------------------------------------------------------------------ the floor displays
def island(n, x, y, w=2.6, d=1.1):
    b(n + "Body", (w, d, 0.55), (x, y, 0.3), "walnut", bevel=0.02); b(n + "Top", (w + 0.1, d + 0.1, 0.05), (x, y, 0.6), "light_oak", bevel=0.012)
    b(n + "Kick", (w - 0.1, d - 0.1, 0.05), (x, y, 0.025), "dark_wood", bevel=0.0)
island("IslandTable", -2.2, -1.4); island("IslandTex", 2.3, -1.4)
for i, (dx, dy, m) in enumerate(((-0.9, -0.2, "ceramic_t"), (-0.3, 0.25, "ceramic"), (0.5, -0.1, "ceramic_b"))): bowls(f"ITB{i}", -2.2 + dx, -1.4 + dy, 0.625, m, 4)
for i, (dx, dy) in enumerate(((-0.6, 0.3), (0.1, -0.28), (0.9, 0.25))): mug(f"ITM{i}", -2.2 + dx, -1.4 + dy, 0.625, ("ceramic_b", "ceramic_t", "ceramic")[i])
vase("ITV", -1.25, -1.5, 0.625, "forest", 0.42); candle("ITC0", -1.75, -1.1, 0.625); candle("ITC1", -2.85, -1.7, 0.625)
c("ITP", 0.13, 0.26, (-3.25, -1.05, 0.755), "ceramic", segs=16)
for i, m in enumerate(("rust", "ochre", "linen_blue", "blush", "forest", "cream")):
    cushion(f"IXC{i}", 1.45 + (i % 3) * 0.72, -1.72 + (i // 3) * 0.62, 0.625, m)
    cushion(f"IXD{i}", 1.5 + (i % 3) * 0.7, -1.7 + (i // 3) * 0.6, 0.78, ("ochre", "forest", "rust", "cream", "linen_blue", "blush")[i])
b("Sign03", (0.72, 0.03, 0.34), (-2.2, -1.4, 1.42), "brand", bevel=0.012); c("Sign03P", 0.012, 0.6, (-2.2, -1.4, 0.94), "brass_m", segs=8)
text_mesh("Sign03T", env, "TABLEWARE", 0.1, M["cream"], (-2.2, -1.42, 1.42), max_w=0.6)
b("Sign04", (0.72, 0.03, 0.34), (2.3, -1.4, 1.42), "brand", bevel=0.012); c("Sign04P", 0.012, 0.6, (2.3, -1.4, 0.94), "brass_m", segs=8)
text_mesh("Sign04T", env, "TEXTILES", 0.1, M["cream"], (2.3, -1.42, 1.42), max_w=0.6)
# front tables and rug
def table(n, x, y, w=1.3):
    b(n, (w, 0.7, 0.05), (x, y, 0.74), "light_oak", bevel=0.012)
    for sx in (-1, 1):
        for sy in (-1, 1): c(f"{n}L{sx}{sy}", 0.025, 0.72, (x + sx * (w / 2 - 0.08), y + sy * 0.27, 0.36), "dark_wood", segs=8)
table("TabA", -1.1, -3.8); table("TabB", 2.6, -3.75)
for i, (dx, m, h) in enumerate(((-0.42, "ceramic_t", 0.36), (0.02, "ceramic", 0.26), (0.42, "ceramic_b", 0.44))): vase(f"TAV{i}", -1.1 + dx, -3.8, 0.765, m, h)
for i in range(4): candle(f"TBC{i}", 2.1 + i * 0.3, -3.65 - (i % 2) * 0.16, 0.765)
throw("TBT", 2.8, -3.95, 0.765, "ochre", 0.5)
c("RugR", 1.25, 0.012, (5.3, -2.6, 0.008), "cream", segs=48); c("RugI", 0.95, 0.014, (5.3, -2.6, 0.009), "rust", segs=48)
def lamp(n, x, y, h=1.6):
    c(n + "B", 0.16, 0.03, (x, y, 0.016), "brass_m", segs=20); c(n + "P", 0.012, h, (x, y, h / 2), "brass_m", segs=8)
    c(n + "S", 0.26, 0.34, (x, y, h + 0.12), "linen", segs=24, r2=0.17); LIGHTS.append((n, (x, y, h + 0.05), 24))
lamp("LampA", 6.7, -1.9, 1.6); lamp("LampB", 4.5, -3.9, 1.3)
b("Armch", (0.85, 0.75, 0.42), (5.4, -2.5, 0.26), "cognac", bevel=0.09); b("ArmchB", (0.85, 0.18, 0.76), (5.4, -2.15, 0.45), "cognac", bevel=0.08)
cushion("ArmchC", 5.4, -2.6, 0.5, "forest")
plant("PlantA", -4.7, 3.95, 1.25); plant("PlantB", 4.6, -0.2, 1.15, "pot_cream"); plant("PlantC", -3.8, -3.9, 1.05, "pot_char"); plant("PlantD", 7.1, 0.6, 1.3)
# rug wall on the right
for i, (y, m, m2) in enumerate(((-3.2, "rust", "ochre"), (-1.9, "forest", "cream"), (-0.5, "linen_blue", "blush"))):
    b(f"RugWall{i}", (0.04, 1.05, 1.9), (XW - 0.03, y, 1.5), m, bevel=0.008)
    for k in range(4): b(f"RugBand{i}{k}", (0.008, 0.95, 0.09), (XW - 0.056, y, 0.82 + k * 0.45), m2, bevel=0.0)
    c(f"RugBar{i}", 0.018, 1.14, (XW - 0.05, y, 2.48), "brass_m", segs=8, rot=(90, 0, 0))
# ------------------------------------------------------------------ the door and the gates
b("DoorFrameT", (0.16, 3.0, 0.14), (-XW - 0.0, -2.7, 2.45), "black_metal", bevel=0.0)
for y in (-4.2, -2.7, -1.2): b(f"DoorFrame{y}", (0.16, 0.12, 2.5), (-XW, y, 1.25), "black_metal", bevel=0.0)
b("DoorGlass", (0.05, 2.9, 2.36), (-XW + 0.02, -2.7, 1.2), "daylight_glass", bevel=0.0)
for i, y in enumerate((-3.4, -2.0)):
    b(f"GatePost{i}", (0.12, 0.2, 1.42), (-5.95, y, 0.71), "steel", bevel=0.02)
    b(f"GateLed{i}", (0.135, 0.05, 1.22), (-5.95, y - 0.0, 0.76), "gateled", bevel=0.0)
    b(f"GatePanel{i}", (0.9, 0.03, 1.0), (-5.5, y, 0.72), "acrylic", bevel=0.004)
# ------------------------------------------------------------------ escalator to the (unseen) upper floor
EX, EL, RAKE = -6.62, 4.9, 30.0
y0, z0 = -0.15, 0.06
cr, sr = math.cos(math.radians(RAKE)), math.sin(math.radians(RAKE))
cm = (y0 + EL * cr / 2, z0 + EL * sr / 2)
for sx in (-1, 1):
    b(f"EscTruss{sx}", (0.14, EL + 0.5, 0.46), (EX + sx * 0.6, cm[0], cm[1] - 0.02), "graphite", bevel=0.02, rot=(RAKE, 0, 0))
    b(f"EscGlass{sx}", (0.022, EL + 0.2, 0.68), (EX + sx * 0.6, cm[0], cm[1] + 0.55), "acrylic", bevel=0.002, rot=(RAKE, 0, 0))
    b(f"EscRail{sx}", (0.075, EL + 0.34, 0.075), (EX + sx * 0.6, cm[0], cm[1] + 0.92), "rubber", bevel=0.03, rot=(RAKE, 0, 0))
b("EscBelly", (1.1, EL + 0.3, 0.1), (EX, cm[0] + 0.1, cm[1] - 0.26), "graphite", bevel=0.0, rot=(RAKE, 0, 0))
b("EscFloorPlate", (1.24, 0.8, 0.03), (EX, y0 - 0.32, 0.03), "steel", bevel=0.004)
b("EscTopPlate", (1.24, 0.64, 0.06), (EX, YB - 0.35, z0 + EL * sr + 0.04), "steel", bevel=0.004)
b("EscTopWall", (1.5, 0.05, 0.65), (EX, YB - 0.03, z0 + EL * sr + 0.38), "graphite", bevel=0.0)
b("EscSign", (1.1, 0.03, 0.3), (EX + 1.25, YB - 0.04, 2.55), "sage_wall", bevel=0.01)
text_mesh("EscSignT", env, "UP · LEVEL 2", 0.11, M["cream"], (EX + 1.25, YB - 0.06, 2.55), max_w=0.95)
for n, y_ in (("EscA", y0), ("EscB", y0 + EL * cr)):
    empty(n, env, (EX, y_, z0 + (y_ - y0) * sr / cr))
# ------------------------------------------------------------------ manager's office
OX = 5.2
b("OfficeFloor", (W / 2 - OX, YB - 1.5, 0.012), ((XW + OX) / 2, (YB + 1.5) / 2, 0.006), "tile", bevel=0.002)
b("OfficeFront", (W / 2 - OX + 0.05, 0.05, 2.5), ((XW + OX) / 2, 1.5, 1.25), "glass_b", bevel=0.0)
b("OfficeSideA", (0.05, 1.7, 2.5), (OX, 2.35, 1.25), "glass_b", bevel=0.0)
b("OfficeSideB", (0.05, 0.4, 2.5), (OX, YB - 0.2, 1.25), "glass_b", bevel=0.0)
b("OfficeHead", (0.08, YB - 1.5, 0.12), (OX, (YB + 1.5) / 2, 2.52), "dark_wood", bevel=0.0); b("OfficeHeadF", (W / 2 - OX, 0.08, 0.12), ((XW + OX) / 2, 1.5, 2.52), "dark_wood", bevel=0.0)
b("OfficeDesk", (1.5, 0.7, 0.05), (6.5, 2.75, 0.74), "walnut"); b("OfficeDeskB", (1.4, 0.04, 0.68), (6.5, 2.42, 0.38), "walnut", bevel=0.0)
b("OfficeBox", (0.3, 0.22, 0.14), (6.05, 2.8, 0.84), "kraft"); b("OfficeLap", (0.36, 0.26, 0.02), (6.85, 2.8, 0.78), "graphite")
text_mesh("OfficePlate", env, "MANAGER", 0.12, M["cream"], (6.5, 1.46, 2.52), max_w=0.8)
b("OfficeShelf", (1.6, 0.26, 0.04), (6.5, YB - 0.14, 1.75), "walnut")
goods("OfficeG", 6.5, YB - 0.14, 1.77, 1.5)
plant("OfficePlant", 7.4, 4.3, 0.95, "pot_cream"); LIGHTS.append(("Office", (6.5, 3.0, 2.3), 22))
# ------------------------------------------------------------------ the cast: jointed figures, facing -Y
ROOTS = []
def person(name, loc, top, pants, hair, sleeve=None, extras=None, skin="skin", shoes="graphite", leg=1.0, girth=0.19, torso=0.68, head_s=1.25):
    """leg scales the legs, girth is the torso radius, torso its length, head_s the head: toy proportions, one silhouette each."""
    coll = make_coll(name); sleeve = M[sleeve or top]; top_m, pants_m, skin_m = M[top], M[pants], M[skin]
    root = empty(name, coll, loc); ROOTS.append(root)
    k = torso / 0.68; hip_z = 0.84 * leg; leg_x = 0.085 + (girth - 0.19) * 0.6
    for sx, t in ((-1, "L"), (1, "R")):
        hip = empty(f"{name}_Leg{t}", coll, (sx * leg_x, 0, hip_z), parent=root)
        capsule_between(f"{name}_Thigh{t}", coll, 0.078, (0, 0, 0), (0, 0, -0.4 * leg), pants_m, parent=hip)
        knee = empty(f"{name}_Knee{t}", coll, (0, 0, -0.42 * leg), parent=hip)
        capsule_between(f"{name}_Shin{t}", coll, 0.066, (0, 0, 0), (0, 0, -0.34 * leg), pants_m, parent=knee)
        box(f"{name}_Shoe{t}", coll, (0.115, 0.22, 0.07), (0, -0.04, -0.385 * leg), M[shoes], bevel=0.03, parent=knee)
    spine = empty(f"{name}_Spine", coll, (0, 0, hip_z + 0.02), parent=root)
    capsule(f"{name}_Torso", coll, girth, torso, (0, 0, 0.2 * k), top_m, parent=spine, sy=0.74)
    head = empty(f"{name}_Head", coll, (0, 0, 0.56 * k), parent=spine); head.scale = (head_s, head_s, head_s)
    cyl(f"{name}_Neck", coll, 0.05, 0.1, (0, 0, 0), skin_m, segs=12, parent=head)
    sphere(f"{name}_Skull", coll, 0.135, (0, 0, 0.11), skin_m, parent=head)
    for sx in (-1, 1):
        sphere(f"{name}_Eye{sx}", coll, 0.02, (sx * 0.048, -0.121, 0.13), M["eye"], parent=head, segs=10, rings=8, scale=(1, 0.6, 1.2))
        sphere(f"{name}_Glint{sx}", coll, 0.006, (sx * 0.042, -0.134, 0.14), M["paper"], parent=head, segs=6, rings=4)
        box(f"{name}_Brow{sx}", coll, (0.05, 0.008, 0.01), (sx * 0.05, -0.128, 0.175), M["hair_dark"], bevel=0.003, parent=head, rot=(0, sx * 9, 0))
        sphere(f"{name}_Cheek{sx}", coll, 0.024, (sx * 0.078, -0.108, 0.078), M["blush"], parent=head, segs=8, rings=6, scale=(1, 0.3, 0.75))
    sphere(f"{name}_Nose", coll, 0.015, (0, -0.135, 0.1), skin_m, parent=head, segs=8, rings=6)
    for i, (x_, z_, r_) in enumerate(((-0.03, 0.058, 16), (-0.012, 0.05, 6), (0.012, 0.05, -6), (0.03, 0.058, -16))):
        box(f"{name}_Smile{i}", coll, (0.022, 0.006, 0.007), (x_, -0.13 + abs(x_) * 0.18, z_), M["burgundy"], bevel=0.0, parent=head, rot=(0, r_, 0))
    hair(name, coll, head)
    sh_x = girth + 0.03
    for sx, t in ((-1, "L"), (1, "R")):
        sh = empty(f"{name}_Arm{t}", coll, (sx * sh_x, 0, 0.43 * k), parent=spine)
        capsule_between(f"{name}_Upper{t}", coll, 0.056, (0, 0, 0), (sx * 0.015, 0, -0.26), sleeve, parent=sh)
        el = empty(f"{name}_Elbow{t}", coll, (sx * 0.015, 0, -0.27), parent=sh)
        capsule_between(f"{name}_Fore{t}", coll, 0.05, (0, 0, 0), (0, -0.01, -0.2), sleeve, parent=el)
        sphere(f"{name}_Hand{t}", coll, 0.048, (0, -0.012, -0.25), skin_m, parent=el, segs=12, rings=8)
    if extras: extras(name, coll, spine, root)
    return root
def robot(name, loc, shell, trim, head_build, leg=0.75, girth=0.17, torso=0.5, head_s=1.0):
    """An AI agent: a round enamel toy with stubby limbs and a big head, on the same joints as a person so it walks and gestures."""
    coll = make_coll(name); S, T = M[shell], M[trim]; joint = M["brass_m"]
    root = empty(name, coll, loc); ROOTS.append(root)
    k = torso / 0.68; hip_z = 0.84 * leg; leg_x = 0.1
    for sx, t in ((-1, "L"), (1, "R")):
        hip = empty(f"{name}_Leg{t}", coll, (sx * leg_x, 0, hip_z), parent=root)
        capsule_between(f"{name}_Thigh{t}", coll, 0.07, (0, 0, 0), (0, 0, -0.38 * leg), S, parent=hip)
        knee = empty(f"{name}_Knee{t}", coll, (0, 0, -0.42 * leg), parent=hip)
        sphere(f"{name}_KneeBall{t}", coll, 0.05, (0, 0, 0), joint, parent=knee, segs=12, rings=8)
        capsule_between(f"{name}_Shin{t}", coll, 0.066, (0, 0, 0), (0, 0, -0.3 * leg), S, parent=knee)
        sphere(f"{name}_Foot{t}", coll, 0.1, (0, -0.04, -0.385 * leg + 0.015), T, parent=knee, segs=16, rings=10, scale=(0.95, 1.3, 0.55))
    spine = empty(f"{name}_Spine", coll, (0, 0, hip_z + 0.02), parent=root)
    sphere(f"{name}_Torso", coll, girth, (0, 0, 0.2 * k), S, parent=spine, scale=(1, 0.88, 1.28 * torso / 0.5), segs=24, rings=16)
    sphere(f"{name}_Tummy", coll, girth * 0.62, (0, -girth * 0.56, 0.17 * k), T, parent=spine, scale=(1, 0.45, 1.1), segs=18, rings=12)
    sphere(f"{name}_Heart", coll, 0.03, (0, -girth * 0.84, 0.22 * k), M["halo"], parent=spine, segs=10, rings=8)
    torus(f"{name}_Collar", coll, 0.078, 0.016, (0, 0, 0.545 * k), M["halo"], parent=spine, rot=(0, 0, 0))
    head = empty(f"{name}_Head", coll, (0, 0, 0.56 * k), parent=spine); head.scale = (head_s, head_s, head_s)
    head_build(name, coll, head)
    sh_x = girth + 0.05
    for sx, t in ((-1, "L"), (1, "R")):
        sh = empty(f"{name}_Arm{t}", coll, (sx * sh_x, 0, 0.43 * k), parent=spine)
        capsule_between(f"{name}_Upper{t}", coll, 0.056, (0, 0, 0), (sx * 0.012, 0, -0.2), S, parent=sh)
        el = empty(f"{name}_Elbow{t}", coll, (sx * 0.012, 0, -0.21), parent=sh)
        sphere(f"{name}_ElbowBall{t}", coll, 0.042, (0, 0, 0), joint, parent=el, segs=12, rings=8)
        capsule_between(f"{name}_Fore{t}", coll, 0.052, (0, 0, 0), (0, -0.01, -0.13), S, parent=el)
        sphere(f"{name}_Hand{t}", coll, 0.075, (0, -0.012, -0.185), T, parent=el, segs=14, rings=10)
def cute_cheeks(n, c_, h, x, y, z):
    for sx in (-1, 1): sphere(f"{n}_Blush{sx}", c_, 0.036, (sx * x, y, z), M["blush_glow"], parent=h, segs=10, rings=8, scale=(1, 0.28, 0.72))
def cute_smile(n, c_, h, z, y, m):
    for i, (x_, z_, r_) in enumerate(((-0.034, z + 0.012, 34), (-0.012, z, 10), (0.012, z, -10), (0.034, z + 0.012, -34))):
        box(f"{n}_Smile{i}", c_, (0.028, 0.008, 0.011), (x_, y, z_), M[m], bevel=0.003, parent=h, rot=(0, r_, 0))
def runner_head(n, c_, h):
    cyl(f"{n}_Neck", c_, 0.04, 0.07, (0, 0, 0.02), M["navy"], segs=10, parent=h)
    sphere(f"{n}_Shell", c_, 0.24, (0, 0, 0.23), M["enamel_ochre"], parent=h, scale=(1.08, 0.92, 0.95), segs=32, rings=22)
    sphere(f"{n}_Screen", c_, 0.19, (0, -0.19, 0.23), M["brand_screen"], parent=h, scale=(1.05, 0.26, 0.76), segs=28, rings=18)
    for sx, t in ((-1, "L"), (1, "R")):
        sphere(f"{n}_Eye{t}", c_, 0.052, (sx * 0.08, -0.236, 0.25), M["visor"], parent=h, segs=18, rings=12, scale=(1, 0.42, 1.1))
        sphere(f"{n}_Glint{t}", c_, 0.015, (sx * 0.08 - 0.018, -0.262, 0.272), M["paper"], parent=h, segs=8, rings=6)
        sphere(f"{n}_Ear{t}", c_, 0.058, (sx * 0.262, 0, 0.23), M["navy"], parent=h, segs=14, rings=10, scale=(0.5, 1, 1))
    cute_cheeks(n, c_, h, 0.135, -0.228, 0.19); cute_smile(n, c_, h, 0.16, -0.238, "visor")
    capsule_between(f"{n}_Aerial", c_, 0.01, (0.05, 0, 0.44), (0.1, 0, 0.56), M["navy"], parent=h)
    sphere(f"{n}_AerialTip", c_, 0.04, (0.11, 0, 0.59), M["halo"], parent=h, segs=12, rings=10)
def reader_head(n, c_, h):
    cyl(f"{n}_Neck", c_, 0.04, 0.07, (0, 0, 0.02), M["enamel_ivory"], segs=10, parent=h)
    sphere(f"{n}_Shell", c_, 0.25, (0, 0, 0.24), M["enamel_sage"], parent=h, scale=(1.04, 0.9, 1.0), segs=32, rings=22)
    for sx, t in ((-1, "L"), (1, "R")):
        x_ = sx * 0.105
        cyl(f"{n}_White{t}", c_, 0.092, 0.014, (x_, -0.213, 0.265), M["paper"], segs=32, parent=h, rot=(90, 0, 0))
        iris = cyl(f"{n}_Iris{t}", c_, 0.06, 0.01, (x_, -0.222, 0.262), M["forest"], segs=26, parent=h, rot=(90, 0, 0))
        cyl(f"{n}_Pupil{t}", c_, 0.04, 0.006, (0, 0, 0.008), M["eye"], segs=20, parent=iris)
        cyl(f"{n}_Glint{t}", c_, 0.016, 0.005, (-0.018, 0.022, 0.013), M["paper"], segs=12, parent=iris)
        torus(f"{n}_Rim{t}", c_, 0.11, 0.019, (x_, -0.228, 0.265), M["brass_m"], parent=h)
        capsule_between(f"{n}_Temple{t}", c_, 0.011, (sx * 0.214, -0.222, 0.27), (sx * 0.262, -0.02, 0.27), M["brass_m"], parent=h)
    capsule_between(f"{n}_Bridge", c_, 0.011, (-0.03, -0.24, 0.285), (0.03, -0.24, 0.285), M["brass_m"], parent=h)
    cute_cheeks(n, c_, h, 0.175, -0.18, 0.13); cute_smile(n, c_, h, 0.1, -0.226, "brand")
    capsule_between(f"{n}_Sprout", c_, 0.011, (0, 0, 0.47), (0, 0, 0.55), M["forest"], parent=h)
    for sx in (-1, 1): sphere(f"{n}_Leaf{sx}", c_, 0.052, (sx * 0.05, 0, 0.58), M["leaf_light"], parent=h, scale=(1.15, 0.45, 0.6), segs=12, rings=8)
def hair_grey(n, c_, h):
    sphere(f"{n}_Hair", c_, 0.146, (0, 0.016, 0.135), M["hair_grey"], parent=h, scale=(1, 1, 0.9), cut_below=0.08)
    for az, rr in ((-60, 0.06), (60, 0.06), (0, 0.065), (-120, 0.06), (120, 0.06), (180, 0.065)):
        a = math.radians(az); sphere(f"{n}_Curl{az}", c_, rr, (math.sin(a) * 0.095, -math.cos(a) * 0.095 + 0.02, 0.2), M["hair_grey"], parent=h, segs=12, rings=8)
def hair_long(n, c_, h):
    sphere(f"{n}_Hair", c_, 0.15, (0, 0.016, 0.13), M["hair_dark"], parent=h, cut_below=-0.02)
    capsule(f"{n}_Back", c_, 0.115, 0.34, (0, 0.085, -0.05), M["hair_dark"], parent=h, sy=0.6)
def hair_brown(n, c_, h):
    sphere(f"{n}_Hair", c_, 0.146, (0, 0.016, 0.145), M["hair_auburn"], parent=h, scale=(1, 1, 0.85), cut_below=0.03)
def tote(name, coll, spine, root):
    arm = bpy.data.objects[f"{name}_ElbowL"]
    box(f"{name}_Tote", coll, (0.05, 0.3, 0.34), (-0.02, -0.01, -0.46), M["cream"], bevel=0.015, parent=arm)
    torus(f"{name}_ToteH", coll, 0.07, 0.008, (-0.02, -0.01, -0.27), M["kraft"], parent=arm, rot=(0, 90, 0))
def manager_things(name, coll, spine, root):
    capsule(f"{name}_Vest", coll, 0.244, 0.68, (0, 0, 0.194), M["burgundy"], parent=spine, sy=0.76)
    box(f"{name}_Collar", coll, (0.14, 0.02, 0.12), (0, -0.18, 0.44), M["white"], bevel=0.01, parent=spine, rot=(-14, 0, 0))
    for sx in (-1, 1):
        capsule_between(f"{name}_Lanyard{sx}", coll, 0.007, (sx * 0.075, -0.15, 0.48), (0, -0.2, 0.2), M["navy"], parent=spine)
    torus(f"{name}_KeyRing", coll, 0.03, 0.006, (0, -0.205, 0.165), M["brass_m"], parent=spine)
    for i, sx in enumerate((-0.03, 0.0, 0.03)):
        box(f"{name}_Key{i}", coll, (0.014, 0.006, 0.085), (sx, -0.21, 0.095 + abs(sx) * 0.4), M["brass_m"], bevel=0.0, parent=spine, rot=(0, sx * 300, 0))
def hair_mustache(n, c_, h):
    hair_grey(n, c_, h)
    for sx in (-1, 1): capsule_between(f"{n}_Tache{sx}", c_, 0.02, (0, -0.138, 0.09), (sx * 0.075, -0.122, 0.078), M["hair_grey"], parent=h)
def nella_things(name, coll, spine, root):
    tote(name, coll, spine, root)
    torus(f"{name}_Scarf", coll, 0.1, 0.038, (0, -0.005, 0.47), M["ochre"], parent=spine, rot=(0, 0, 0))
    capsule_between(f"{name}_ScarfTail", coll, 0.034, (0.05, -0.15, 0.44), (0.07, -0.2, 0.18), M["ochre"], parent=spine)
person("Nella", (-7.0, -2.6, 0), "rust", "pants_dark", hair_long, extras=nella_things, leg=0.8, girth=0.215, torso=0.56, head_s=1.32)
robot("Reader", (-2.6, 3.42, 0), "enamel_sage", "enamel_ivory", reader_head, leg=0.86, girth=0.16, torso=0.54)
robot("Runner", (-0.4, 3.42, 0), "enamel_ochre", "navy", runner_head, leg=0.76, girth=0.185, torso=0.5)
person("Manager", (6.45, 3.55, 0), "white", "pants_dark", hair_mustache, extras=manager_things, leg=0.94, girth=0.236, torso=0.66, head_s=1.22)
person("Shopper1", (-4.6, 0.6, 0), "ochre", "pants", hair_brown, leg=0.92, girth=0.2, torso=0.62)
person("Shopper2", (4.4, 0.5, 0), "linen_blue", "pants_dark", hair_long, leg=1.05, girth=0.165, torso=0.66)
# the two machines on the counter
coll = make_coll("Machines")
cf = empty("Counterfoil", coll, (1.3, CY, TOP)); ROOTS.append(cf)
box("CF_Body", coll, (0.78, 0.5, 0.52), (0, 0.02, 0.26), M["walnut"], bevel=0.03, parent=cf)
box("CF_Trim", coll, (0.82, 0.54, 0.035), (0, 0.02, 0.53), M["brass_m"], bevel=0.008, parent=cf)
box("CF_Face", coll, (0.6, 0.012, 0.28), (0, -0.23, 0.33), M["brand"], bevel=0.0, parent=cf)
text_mesh("CF_Name", coll, "COUNTERFOIL", 0.075, M["cream"], (0, -0.238, 0.37), parent=cf, max_w=0.52)
text_mesh("CF_Sub", coll, "CHECKS THE RECORD", 0.03, M["cream"], (0, -0.238, 0.29), parent=cf, max_w=0.44)
box("CF_Status", coll, (0.6, 0.014, 0.035), (0, -0.232, 0.13), M["gateled"], bevel=0.0, parent=cf)
box("CF_Pad", coll, (0.24, 0.2, 0.022), (0.57, -0.26, 0.012), M["graphite"], bevel=0.006, parent=cf)
cyl("CF_Post", coll, 0.03, 0.54, (0.57, 0.12, 0.27), M["brass_m"], segs=10, parent=cf)
arm = empty("Counterfoil_Arm", coll, (0.57, 0.12, 0.53), parent=cf)
box("CF_ArmBar", coll, (0.05, 0.44, 0.05), (0, -0.2, 0), M["brass_m"], bevel=0.012, parent=arm)
cyl("CF_StampStem", coll, 0.022, 0.12, (0, -0.38, -0.07), M["brass_m"], segs=10, parent=arm)
cyl("CF_StampHead", coll, 0.08, 0.07, (0, -0.38, -0.16), M["burgundy"], segs=20, parent=arm)
pp = empty("PayPal", coll, (3.05, CY, TOP)); ROOTS.append(pp)
box("PP_Body", coll, (0.52, 0.34, 0.66), (0, 0.04, 0.33), M["brand"], bevel=0.05, parent=pp)
box("PP_Face", coll, (0.4, 0.012, 0.3), (0, -0.135, 0.44), M["brand_screen"], bevel=0.0, parent=pp)
text_mesh("PP_T", coll, "SANDBOX", 0.06, M["sign"], (0, -0.143, 0.47), parent=pp, max_w=0.34)
text_mesh("PP_Sub", coll, "PAYMENT RAIL", 0.03, M["cream"], (0, -0.143, 0.4), parent=pp, max_w=0.3)
for i in range(3): box(f"PP_Key{i}", coll, (0.1, 0.02, 0.06), (-0.13 + i * 0.13, -0.135, 0.18), M["cream"], bevel=0.008, parent=pp)
box("PP_Slot", coll, (0.3, 0.02, 0.018), (0, -0.135, 0.08), M["graphite"], bevel=0.0, parent=pp)
# ------------------------------------------------------------------ lights (the page builds these)
for n, loc, power in LIGHTS:
    o = empty(f"Lamp_{n}", env, loc); o["power"] = power
# ------------------------------------------------------------------ one mesh per material for everything that never moves
bpy.context.view_layer.update()
keep = set()
for r in ROOTS:
    keep.add(r); keep.update(r.children_recursive)
groups = {}
for ob in list(scene.objects):
    if ob.type != "MESH" or ob in keep or not ob.data.materials: continue
    groups.setdefault(ob.data.materials[0].name, []).append(ob)
for name, obs in groups.items():
    bm = bmesh.new()
    for ob in obs:
        me = ob.data.copy(); me.transform(ob.matrix_world); bm.from_mesh(me); bpy.data.meshes.remove(me)
    mat_ = obs[0].data.materials[0]
    for ob in obs: bpy.data.objects.remove(ob)
    finish_mesh(bm, f"Store_{name}", env, mat_, (0, 0, 0), None)
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in scene.objects if o.type == "MESH")
print(f"HOMI_STATS objects={len(scene.objects)} meshes={sum(o.type == 'MESH' for o in scene.objects)} tris={tris}")
bpy.ops.export_scene.gltf(filepath=os.path.join(WORLD, "homi-store.glb"), export_format="GLB", use_selection=False, export_apply=True, export_extras=True, export_cameras=False, export_lights=False, export_yup=True, export_animations=False)

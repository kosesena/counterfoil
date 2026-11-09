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
    "brand": mat("M_HomiNavy", "#21365c", 0.5), "sign": mat("M_SignGlow", "#fff0d6", 0.3, emit="#ffd9a0", emit_strength=3.2),
    "brand_screen": mat("M_ScreenNavy", "#142238", 0.3, emit="#1d3a66", emit_strength=0.9), "brass_m": mat("M_Brass", "#c9a35f", 0.28, metal=0.85),
    "tile": mat("M_TileEntry", "#e8ddca", 0.5), "rubber": mat("M_Rubber", "#2c2d30", 0.6), "esc_step": mat("M_EscStep", "#7c8087", 0.4, metal=0.5),
    "acrylic": mat("SE_GateAcrylic", "#e6f2f6", 0.05, alpha=0.3), "glass_b": mat("M_OfficeGlass", "#dcebf0", 0.05, alpha=0.1),
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
oak = bpy.data.materials.new("M_FloorOak"); oak.use_nodes = True
nt = oak.node_tree; bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
for key, fn, data in (("Base Color", "floor-oak.jpg", False), ("Normal", "floor-oak-nor.jpg", True)):
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(WORLD, fn)); t.image.pack()
    if data:
        t.image.colorspace_settings.name = "Non-Color"; n = nt.nodes.new("ShaderNodeNormalMap"); n.inputs["Strength"].default_value = 0.7
        nt.links.new(t.outputs["Color"], n.inputs["Color"]); nt.links.new(n.outputs["Normal"], bsdf.inputs["Normal"])
    else:
        nt.links.new(t.outputs["Color"], bsdf.inputs[key])
bsdf.inputs["Roughness"].default_value = 0.36
floor = rounded_slab("Floor", env, W, D, 0.006, 0.18, (0, 0, 0.0005), oak, edge_bevel=0.002)
uv = floor.data.uv_layers.new(name="UVMap")
for lp in floor.data.loops:
    co = floor.data.vertices[lp.vertex_index].co; uv.data[lp.index].uv = (co.x / 1.7, co.y / 1.7)
b("EntryMat", (2.4, 3.0, 0.012), (-6.5, -2.7, 0.006), "brand", bevel=0.003)
b("WallBack", (W + 0.3, 0.2, H), (0, YB + 0.1, H / 2), "plaster")
for sx, nm in ((-1, "L"), (1, "R")):
    b(f"Wall{nm}Lo", (0.2, D, H), (sx * (XW + 0.1), 0, H / 2), "plaster")
    b(f"Cap{nm}", (0.26, D + 0.3, 0.08), (sx * (XW + 0.1), 0, H + 0.04), "walnut")
b("CapBack", (W + 0.5, 0.26, 0.08), (0, YB + 0.1, H + 0.04), "walnut")
# wainscot on all walls
wg = groove_material("M_Fluted", "#5f4230"); wa = groove_material("M_Wains", "#8fa389", 0.75)
for nm, w_, loc, rz in (("BackL", 4.3, (-5.6, YB - 0.005, 0.6), 0), ("BackR", 2.8, (6.4, YB - 0.005, 0.6), 0)):
    face_plane(f"Wains{nm}", env, w_, 1.2, loc, wa)
# left wall: fluted sage below, posters above; string lights along both side walls and the back
fp = face_plane("WainsLeft", env, 5.6, 1.2, (0, 0, 0), wa); fp.rotation_euler = (0, 0, math.radians(-90)); fp.location = (-XW + 0.006, 1.9, 0.6)
b("WainsCapL", (0.04, 5.6, 0.04), (-XW + 0.02, 1.9, 1.22), "walnut", bevel=0.004)
b("WainsCapB", (4.3, 0.04, 0.04), (-5.6, YB - 0.02, 1.22), "walnut", bevel=0.004)
for i, (y, m, t_) in enumerate(((0.2, "teal", "SLOW"), (1.55, "mustard", "HOME"), (2.9, "rust", "MADE"))):
    b(f"Poster{i}", (0.03, 0.82, 1.08), (-XW + 0.018, y, 2.0), "walnut", bevel=0.004)
    b(f"PosterF{i}", (0.01, 0.72, 0.98), (-XW + 0.036, y, 2.0), m, bevel=0.0)
    tx = text_mesh(f"PosterT{i}", env, t_, 0.2, M["cream"], (-XW + 0.044, y, 2.0), rot=(90, 0, 90), max_w=0.58)
def strand(n, a_, b_, count, sag=0.16):
    a_, b_ = Vector(a_), Vector(b_); prev = a_
    for i in range(1, count + 1):
        u = i / count; p_ = a_.lerp(b_, u); p_.z -= sag * 4 * u * (1 - u)
        capsule_between(f"{n}W{i}", env, 0.005, tuple(prev), tuple(p_), M["black_metal"])
        s_ = p_.copy(); s_.z -= 0.05
        s(f"{n}B{i}", 0.04, tuple(s_), "fairy", segs=8, rings=6); prev = p_
for n, a_, b_ in (("StrA", (-XW + 0.1, -4.6, 2.86), (-XW + 0.1, -0.3, 2.86)), ("StrB", (XW - 0.1, -4.6, 2.86), (XW - 0.1, 0.0, 2.86)), ("StrC", (XW - 0.1, 0.0, 2.86), (XW - 0.1, 1.4, 2.86)), ("StrD", (4.3, YB - 0.1, 2.86), (XW - 0.1, YB - 0.1, 2.86))):
    strand(n, a_, b_, 14)
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
bay("BayL", -3.1, 2.3); bay("BayR", 3.1, 2.3)
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
for i, x in enumerate((-3.7, -1.5, 0.75, 2.35, 3.9)):
    if abs(x + 0.4) < 0.3: continue
    c(f"PendW{i}", 0.005, 0.42, (x, CY + 0.02, 2.6), "black_metal", segs=6)
    sphere(f"PendS{i}", env, 0.2, (x, CY + 0.02, 2.2), M["rattan"], scale=(1, 1, 1.12), segs=20, rings=12)
    torus(f"PendB{i}", env, 0.2, 0.012, (x, CY + 0.02, 2.2), M["rattan_dark"], rot=(0, 0, 0))
    s(f"PendG{i}", 0.05, (x, CY + 0.02, 1.98), "bulb", segs=10, rings=8); LIGHTS.append((f"Pend{i}", (x, CY - 0.15, 1.9), 26))
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
def person(name, loc, top, pants, hair, sleeve=None, extras=None, skin="skin", shoes="graphite"):
    coll = make_coll(name); sleeve = M[sleeve or top]; top_m, pants_m, skin_m = M[top], M[pants], M[skin]
    root = empty(name, coll, loc); ROOTS.append(root)
    for sx, t in ((-1, "L"), (1, "R")):
        hip = empty(f"{name}_Leg{t}", coll, (sx * 0.085, 0, 0.84), parent=root)
        capsule_between(f"{name}_Thigh{t}", coll, 0.078, (0, 0, 0), (0, 0, -0.4), pants_m, parent=hip)
        knee = empty(f"{name}_Knee{t}", coll, (0, 0, -0.42), parent=hip)
        capsule_between(f"{name}_Shin{t}", coll, 0.066, (0, 0, 0), (0, 0, -0.34), pants_m, parent=knee)
        box(f"{name}_Shoe{t}", coll, (0.115, 0.22, 0.07), (0, -0.04, -0.385), M[shoes], bevel=0.03, parent=knee)
    spine = empty(f"{name}_Spine", coll, (0, 0, 0.86), parent=root)
    capsule(f"{name}_Torso", coll, 0.19, 0.68, (0, 0, 0.2), top_m, parent=spine, sy=0.72)
    head = empty(f"{name}_Head", coll, (0, 0, 0.56), parent=spine)
    cyl(f"{name}_Neck", coll, 0.05, 0.1, (0, 0, 0), skin_m, segs=12, parent=head)
    sphere(f"{name}_Skull", coll, 0.135, (0, 0, 0.11), skin_m, parent=head)
    for sx in (-1, 1):
        sphere(f"{name}_Eye{sx}", coll, 0.015, (sx * 0.046, -0.125, 0.125), M["eye"], parent=head, segs=8, rings=6)
    box(f"{name}_Mouth", coll, (0.04, 0.006, 0.006), (0, -0.131, 0.06), M["burgundy"], bevel=0.0, parent=head)
    hair(name, coll, head)
    for sx, t in ((-1, "L"), (1, "R")):
        sh = empty(f"{name}_Arm{t}", coll, (sx * 0.215, 0, 0.43), parent=spine)
        capsule_between(f"{name}_Upper{t}", coll, 0.056, (0, 0, 0), (sx * 0.015, 0, -0.26), sleeve, parent=sh)
        el = empty(f"{name}_Elbow{t}", coll, (sx * 0.015, 0, -0.27), parent=sh)
        capsule_between(f"{name}_Fore{t}", coll, 0.05, (0, 0, 0), (0, -0.01, -0.2), sleeve, parent=el)
        sphere(f"{name}_Hand{t}", coll, 0.048, (0, -0.012, -0.25), skin_m, parent=el, segs=12, rings=8)
    if extras: extras(name, coll, spine, root)
    return root
def apron(colour):
    def f(name, coll, spine, root):
        box(f"{name}_Apron", coll, (0.34, 0.03, 0.54), (0, -0.14, 0.12), M[colour], bevel=0.02, parent=spine)
        box(f"{name}_Bib", coll, (0.22, 0.03, 0.2), (0, -0.14, 0.41), M[colour], bevel=0.015, parent=spine)
        box(f"{name}_Pocket", coll, (0.17, 0.008, 0.08), (0, -0.157, 0.05), M["cream"], bevel=0.004, parent=spine)
        cyl(f"{name}_Badge", coll, 0.03, 0.006, (0.07, -0.158, 0.41), M["brass_m"], segs=14, parent=spine, rot=(90, 0, 0))
    return f
def hair_bun(n, c_, h):
    sphere(f"{n}_Hair", c_, 0.148, (0, 0.012, 0.128), M["hair_auburn"], parent=h, scale=(1, 1, 0.95), cut_below=-0.05)
    sphere(f"{n}_Bun", c_, 0.07, (0, 0.11, 0.22), M["hair_auburn"], parent=h, segs=14, rings=8)
    for sx in (-1, 1): torus(f"{n}_Lens{sx}", c_, 0.031, 0.0045, (sx * 0.047, -0.137, 0.125), M["graphite"], parent=h)
    box(f"{n}_Bridge", c_, (0.03, 0.008, 0.008), (0, -0.139, 0.13), M["graphite"], bevel=0.0, parent=h)
def hair_cap(n, c_, h):
    sphere(f"{n}_Hair", c_, 0.145, (0, 0.015, 0.14), M["hair_dark"], parent=h, scale=(1, 1, 0.85), cut_below=0.05)
    sphere(f"{n}_Cap", c_, 0.15, (0, 0.0, 0.17), M["navy"], parent=h, scale=(1, 1, 0.72), cut_below=0.2)
    box(f"{n}_Peak", c_, (0.2, 0.13, 0.02), (0, -0.15, 0.185), M["navy"], bevel=0.008, parent=h)
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
def vest(name, coll, spine, root):
    capsule(f"{name}_Vest", coll, 0.198, 0.62, (0, 0, 0.2), M["burgundy"], parent=spine, sy=0.74)
    box(f"{name}_Collar", coll, (0.12, 0.02, 0.12), (0, -0.14, 0.44), M["white"], bevel=0.01, parent=spine, rot=(-12, 0, 0))
person("Nella", (-7.0, -2.6, 0), "rust", "pants_dark", hair_long, extras=tote)
person("Reader", (-2.6, 3.42, 0), "green", "pants", hair_bun, extras=apron("cream"))
person("Runner", (-0.4, 3.42, 0), "white", "pants_dark", hair_cap, extras=apron("navy"))
person("Manager", (6.45, 3.55, 0), "white", "pants_dark", hair_grey, extras=vest)
person("Shopper1", (-4.6, 0.6, 0), "ochre", "pants", hair_brown)
person("Shopper2", (4.4, 0.5, 0), "linen_blue", "pants_dark", hair_long)
# the two machines on the counter
coll = make_coll("Machines")
cf = empty("Counterfoil", coll, (1.3, CY, TOP)); ROOTS.append(cf)
box("CF_Body", coll, (0.78, 0.5, 0.52), (0, 0.02, 0.26), M["walnut"], bevel=0.03, parent=cf)
box("CF_Trim", coll, (0.82, 0.54, 0.035), (0, 0.02, 0.53), M["brass_m"], bevel=0.008, parent=cf)
box("CF_Face", coll, (0.6, 0.012, 0.28), (0, -0.23, 0.33), M["brand_screen"], bevel=0.0, parent=cf)
text_mesh("CF_Name", coll, "COUNTERFOIL", 0.075, M["sign"], (0, -0.238, 0.37), parent=cf, max_w=0.52)
text_mesh("CF_Sub", coll, "CHECKS THE RECORD", 0.03, M["cream"], (0, -0.238, 0.29), parent=cf, max_w=0.44)
box("CF_Status", coll, (0.6, 0.014, 0.035), (0, -0.232, 0.13), M["gateled"], bevel=0.0, parent=cf)
box("CF_Pad", coll, (0.3, 0.26, 0.022), (0, -0.46, 0.012), M["graphite"], bevel=0.006, parent=cf)
post = cyl("CF_Post", coll, 0.03, 0.34, (0.3, 0.14, 0.72), M["brass_m"], segs=10, parent=cf)
arm = empty("Counterfoil_Arm", coll, (0, 0.14, 0.86), parent=cf)
box("CF_Beam", coll, (0.66, 0.05, 0.05), (0.0, 0, 0), M["brass_m"], bevel=0.012, parent=arm)
box("CF_ArmBar", coll, (0.05, 0.6, 0.05), (0, -0.3, 0), M["brass_m"], bevel=0.012, parent=arm)
cyl("CF_StampStem", coll, 0.024, 0.2, (0, -0.6, -0.1), M["brass_m"], segs=10, parent=arm)
cyl("CF_StampHead", coll, 0.1, 0.08, (0, -0.6, -0.23), M["burgundy"], segs=20, parent=arm)
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

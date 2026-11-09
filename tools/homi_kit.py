"""Blender helpers for the HOMI store: materials and rounded primitives. Imported by build_homi_store.py."""
import math, os, random, sys
import bmesh, bpy
from mathutils import Matrix, Vector
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
# ---------------------------------------------------------------- materials
def srgb(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexcol(h):
    h = h.lstrip("#")
    return tuple(srgb(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))


MATS = {}


def mat(name, hexc, rough=0.65, emit=None, emit_strength=0.0, alpha=1.0, metal=0.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    col = hexcol(hexc)
    bsdf.inputs["Base Color"].default_value = (*col, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    m.diffuse_color = (*col, alpha)
    if emit:
        ec = hexcol(emit)
        for key in ("Emission Color", "Emission"):
            if key in bsdf.inputs:
                bsdf.inputs[key].default_value = (*ec, 1.0)
                break
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
            try:
                setattr(m, attr, val)
            except Exception:
                pass
        try:
            m.use_backface_culling = False
        except Exception:
            pass
    MATS[name] = m
    return m


M = {
    "white": mat("M_White", "#d8cfc2", 0.7),  # warm greige (no pure white)
    "platform": mat("M_Platform", "#8a7a6a", 0.8),  # warm taupe base
    "offwhite": mat("M_OffWhite", "#5a4030", 0.7),  # shelf backs (dark walnut)
    "wood": mat("M_Wood", "#d9c7ad", 0.7),
    "wood_dark": mat("M_WoodDark", "#a88a6a", 0.7),
    "grey": mat("M_Grey", "#c9c9c7", 0.6),
    "graphite": mat("M_Graphite", "#3b3f45", 0.5),
    "steel": mat("M_Steel", "#b8bcc2", 0.35, metal=0.6),
    "green": mat("M_MutedGreen", "#6b8a74", 0.7),
    "green_dark": mat("M_MutedGreenDark", "#4f6a57", 0.7),
    "walnut": mat("M_Walnut", "#6e4b34", 0.55),
    "dark_wood": mat("M_DarkWood", "#4a3426", 0.5),
    "kraft": mat("M_Kraft", "#b98a5e", 0.8),
    "slat_oak": mat("M_SlatOak", "#d9c7a8", 0.6),
    "slat_oak2": mat("M_SlatOakAccent", "#c4ab84", 0.6),
    "light_oak": mat("M_LightOak", "#d2b48c", 0.5),
    "cognac": mat("M_LeatherCognac", "#b9733a", 0.38),
    "ottoman": mat("M_LeatherGreyBrown", "#5b4a40", 0.45),
    "black_metal": mat("M_BlackMetal", "#262626", 0.35, metal=0.6),
    "rattan": mat("M_Rattan", "#c89b62", 0.8, emit="#ffc27a", emit_strength=0.35),
    "rattan_dark": mat("M_RattanWeave", "#9a7044", 0.85),
    "linen": mat("M_LinenShade", "#efe4cf", 0.8, emit="#ffd9a0", emit_strength=0.6),
    "led_2700": mat("M_LED2700K", "#ffd2a0", 0.3, emit="#ffb46b", emit_strength=4.0),
    "led_2700_soft": mat("M_LED2700KSoft", "#ffd2a0", 0.3, emit="#ffb46b", emit_strength=1.6),
    "brass_band": mat("M_BrushedBrass", "#c9a35f", 0.3, metal=0.85),
    "teal": mat("M_PosterTeal", "#2f7f7a", 0.8),
    "mustard": mat("M_PosterMustard", "#d6a630", 0.8),
    "screen_green": mat("M_ScreenGreen", "#1f3d33", 0.4, emit="#2c5a49", emit_strength=0.7),
    "screen_text": mat("M_ScreenText", "#f1e9d8", 0.4, emit="#f1e9d8", emit_strength=0.9),
    "daylight_glass": mat("M_DaylightGlass", "#d6ecf5", 0.05, emit="#e3f2fa", emit_strength=0.5, alpha=0.45),
    "wall_green": mat("M_WallSage", "#7e9478", 0.85),  # muted sage
    "wall_espresso": mat("M_WallCream", "#eadbc4", 0.9),  # warm cream plaster
    "dark_cabinet": mat("M_DarkCabinet", "#5a3e2b", 0.6),  # dark walnut
    "counter_top": mat("M_CounterTopWalnut", "#4a3426", 0.35),
    "dark_grey": mat("M_DarkGrey", "#5a4a3e", 0.6),
    "oak_edge_d": mat("M_DeskLeg", "#4f3828", 0.55),
    "holiday_red": mat("M_HolidayRed", "#a8322d", 0.45),
    "fir": mat("M_Fir", "#2d4f3c", 0.85),
    "fir_light": mat("M_FirLight", "#3b6249", 0.85),
    "gold": mat("M_Gold", "#d4a94f", 0.25, metal=0.8),
    "fairy": mat("M_FairyLight", "#ffd08a", 0.3, emit="#ffc766", emit_strength=3.5),  # daytime: subtler
    "pot_cream": mat("M_PotCream", "#e9e2d4", 0.6),
    "pot_char": mat("M_PotCharcoal", "#45484d", 0.6),
    "slate": mat("M_ChalkSlate", "#2f3534", 0.85),
    "chalk": mat("M_Chalk", "#e9e1cc", 0.9),
    "brass": mat("M_ShadeOchre", "#c99a5b", 0.45, metal=0.2),
    "bulb": mat("M_WarmBulb", "#ffe2b0", 0.3, emit="#ffb46b", emit_strength=6.0),  # ~2700K, daytime
    "leaf": mat("M_Leaf", "#5e8560", 0.75),
    "leaf_light": mat("M_LeafLight", "#7b9d6f", 0.75),
    "soil": mat("M_Soil", "#4a3a2c", 0.95),
    "pastry": mat("M_Pastry", "#d9a15b", 0.6),
    "pastry_dark": mat("M_PastryDark", "#8a5a3c", 0.6),
    "glaze": mat("M_Glaze", "#eedcc0", 0.5),
    "rust": mat("M_Rust", "#b0644a", 0.7),
    "navy": mat("M_Navy", "#33415e", 0.65),
    "cream": mat("M_Cream", "#efe5cf", 0.7),
    "burgundy": mat("M_Burgundy", "#7a2e3b", 0.65),
    "apron": mat("M_ApronBrown", "#7a573f", 0.75),
    "skin": mat("M_Skin", "#efcfb6", 0.6),
    "hair_dark": mat("M_HairDark", "#4a3a2f", 0.7),
    "hair_grey": mat("M_HairGrey", "#bdbbb8", 0.7),
    "hair_auburn": mat("M_HairAuburn", "#8a5a3c", 0.7),
    "eye": mat("M_Eye", "#2a2a2e", 0.4),
    "pants": mat("M_PantsGrey", "#5d6168", 0.7),
    "pants_dark": mat("M_PantsDark", "#3c4049", 0.7),
    "hood": mat("M_HoodSlate", "#626873", 0.8),
    "hood_inside": mat("M_HoodShadow", "#16171a", 0.9),
    "ink": mat("M_Ink", "#1b1f3a", 0.3),
    "paper": mat("M_Paper", "#fbf8f1", 0.8),
    "glass": mat("M_Glass", "#dfeef5", 0.05, alpha=0.18),
    "alarm": mat("M_AlarmRed", "#e0322a", 0.4, emit="#ff2a1f", emit_strength=4.0, alpha=0.45),
    "blue_led": mat("M_StatusBlue", "#2f7bff", 0.3, emit="#2f7bff", emit_strength=6.0),
    "amber": mat("M_GateAmber", "#e07a1f", 0.3, emit="#ff7a0a", emit_strength=2.2),
    "screen": mat("M_Screen", "#26303d", 0.25, emit="#8fb4d9", emit_strength=0.6),
    "cup": mat("M_Cup", "#ebe4d8", 0.4),
    "coffee": mat("M_Coffee", "#5a3b28", 0.3),
}


EXTRA_LIGHTS = []  # (name, location, power) recreated as warm point lights in the lighting section

# ---------------------------------------------------------------- collections & objects
def make_coll(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c


def link(obj, coll):
    coll.objects.link(obj)
    return obj


def empty(name, coll, loc=(0, 0, 0), rot_z=0.0, parent=None):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "PLAIN_AXES"
    e.empty_display_size = 0.2
    e.location = loc
    e.rotation_euler = (0, 0, math.radians(rot_z))
    link(e, coll)
    if parent:
        e.parent = parent
    return e


def finish_mesh(bm, name, coll, material, loc, parent, smooth_angle=None, rot=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth_angle is not None:
        for p in me.polygons:
            p.use_smooth = True
        try:
            me.set_sharp_from_angle(angle=math.radians(smooth_angle))
        except Exception:
            pass
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    if rot:
        ob.rotation_euler = [math.radians(a) for a in rot]
    link(ob, coll)
    if parent:
        ob.parent = parent
    return ob


def box(name, coll, size, loc, material, bevel=0.012, segs=2, parent=None, rot=None, smooth=30):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges) + list(bm.verts), offset=bevel,
                        segments=segs, affect="EDGES", profile=0.5)
    return finish_mesh(bm, name, coll, material, loc, parent, smooth, rot)


def rounded_slab(name, coll, sx, sy, sz, radius, loc, material, parent=None, edge_bevel=0.05):
    """Box with rounded vertical corners + soft top/bottom edge."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((sx, sy, sz)), verts=bm.verts)
    vert_edges = [e for e in bm.edges
                  if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-4]
    bmesh.ops.bevel(bm, geom=vert_edges, offset=radius, segments=10,
                    affect="EDGES", profile=0.5)
    horiz = [e for e in bm.edges
             if abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-4
             and len(e.link_faces) == 2
             and any(abs(f.normal.z) > 0.9 for f in e.link_faces)]
    bmesh.ops.bevel(bm, geom=horiz, offset=edge_bevel, segments=4,
                    affect="EDGES", profile=0.5)
    return finish_mesh(bm, name, coll, material, loc, parent, 40)


def cyl(name, coll, r, depth, loc, material, segs=20, parent=None, rot=None, r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r, radius2=r if r2 is None else r2, depth=depth)
    return finish_mesh(bm, name, coll, material, loc, parent, 40, rot)


def sphere(name, coll, r, loc, material, scale=(1, 1, 1), parent=None, segs=20, rings=12,
           cut_below=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    if cut_below is not None:
        doomed = [v for v in bm.verts if v.co.z < cut_below * r - 1e-5]
        bmesh.ops.delete(bm, geom=doomed, context="VERTS")
        edges = [e for e in bm.edges if e.is_boundary]
        if edges:
            bmesh.ops.holes_fill(bm, edges=edges, sides=0)
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    return finish_mesh(bm, name, coll, material, loc, parent, 60)


def capsule(name, coll, r, length, loc, material, parent=None, rot=None, sy=1.0, sx=1.0,
            segs=18, rings=12):
    """Capsule along local Z, total length = length (incl. caps), centred on loc."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    half = max(0.0, length / 2 - r)
    for v in bm.verts:
        if v.co.z > 1e-6:
            v.co.z += half
        elif v.co.z < -1e-6:
            v.co.z -= half
    bmesh.ops.scale(bm, vec=Vector((sx, sy, 1.0)), verts=bm.verts)
    return finish_mesh(bm, name, coll, material, loc, parent, 60, rot)


def capsule_between(name, coll, r, a, b, material, parent=None):
    a, b = Vector(a), Vector(b)
    d = b - a
    ob = capsule(name, coll, r, d.length + 2 * r, (a + b) / 2, material, parent)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return ob


def torus(name, coll, R, r, loc, material, parent=None, rot=(90, 0, 0)):
    bm = bmesh.new()
    seg_major, seg_minor = 20, 6
    verts = []
    for i in range(seg_major):
        u = 2 * math.pi * i / seg_major
        ring = []
        for j in range(seg_minor):
            v = 2 * math.pi * j / seg_minor
            x = (R + r * math.cos(v)) * math.cos(u)
            y = (R + r * math.cos(v)) * math.sin(u)
            z = r * math.sin(v)
            ring.append(bm.verts.new((x, y, z)))
        verts.append(ring)
    for i in range(seg_major):
        for j in range(seg_minor):
            a = verts[i][j]
            b = verts[(i + 1) % seg_major][j]
            c = verts[(i + 1) % seg_major][(j + 1) % seg_minor]
            d = verts[i][(j + 1) % seg_minor]
            bm.faces.new((a, b, c, d))
    return finish_mesh(bm, name, coll, material, loc, parent, 60, rot)



def text_mesh(name, coll, body, size, mat_, loc, rot=(90, 0, 0), parent=None, max_w=None,
              extrude=0.0, font=None):
    """Blender text converted to a flat mesh (centred), optionally scaled to max_w."""
    cu = bpy.data.curves.new(name + "_curve", "FONT")
    cu.resolution_u = 2  # light glyph tessellation for the web
    if font is not None:
        cu.font = font
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    scene.collection.objects.link(tmp)
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    me.name = name
    if max_w and len(me.vertices):
        w = max(v.co.x for v in me.vertices) - min(v.co.x for v in me.vertices)
        if w > max_w:
            for v in me.vertices:
                v.co *= max_w / w
    me.materials.append(mat_)
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot]
    link(ob, coll)
    if parent:
        ob.parent = parent
    return ob


def add_planar_uv(ob, scale_u, scale_v, axes=("x", "y")):
    me = ob.data
    uv = me.uv_layers.new(name="UVMap")
    for lp in me.loops:
        co = me.vertices[lp.vertex_index].co
        uv.data[lp.index].uv = (getattr(co, axes[0]) * scale_u, getattr(co, axes[1]) * scale_v)


def tex_material(name, img, rough=0.6, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    if emit:
        ekey = "Emission Color" if "Emission Color" in bsdf.inputs else "Emission"
        nt.links.new(tex.outputs["Color"], bsdf.inputs[ekey])
        bsdf.inputs["Emission Strength"].default_value = emit
    return m


def np_image(name, rgb):
    """rgb: HxWx3 float array in sRGB 0..1 -> packed Blender image."""
    import numpy as _np
    h, w = rgb.shape[:2]
    rgba = _np.ones((h, w, 4), dtype=_np.float32)
    rgba[..., :3] = _np.clip(rgb, 0, 1)
    im = bpy.data.images.new(name, w, h, alpha=False)
    im.pixels.foreach_set(rgba.ravel())
    im.pack()
    return im


def hex_srgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def groove_material(name, hexc, groove=0.62):
    """Vertical-groove panelling: one groove per texture tile (tile = 6 cm)."""
    import numpy as _np
    c = _np.array(hex_srgb(hexc))
    img = _np.tile(c, (8, 64, 1)).astype(_np.float32)
    img[:, :5] *= groove          # groove shadow
    img[:, 5:9] *= 1.06           # lit edge
    img[:, 56:] *= 0.93
    return tex_material(name, np_image(name + "_img", img), 0.7)


def grooved_panel(name, coll, w, h, loc, mat_, parent=None, rot_z=0.0, pitch=0.06):
    ob = face_plane(name, coll, w, h, loc, mat_, parent)
    for lp in ob.data.uv_layers[0].data:
        lp.uv = (lp.uv[0] * w / pitch, lp.uv[1])
    ob.rotation_euler = (0, 0, math.radians(rot_z))
    return ob


def face_plane(name, coll, w, h, loc, material, parent=None):
    """Plane in local XZ facing -Y with clean 0-1 UVs (u = left->right, v = bottom->top)."""
    bm = bmesh.new()
    vs = [bm.verts.new(c) for c in ((-w / 2, 0, -h / 2), (w / 2, 0, -h / 2),
                                    (w / 2, 0, h / 2), (-w / 2, 0, h / 2))]
    f = bm.faces.new(vs)
    bm.normal_update()
    if f.normal.y > 0:
        f.normal_flip()
    uv = bm.loops.layers.uv.new("UVMap")
    for lp in f.loops:
        co = lp.vert.co
        lp[uv].uv = ((co.x + w / 2) / w, (co.z + h / 2) / h)
    return finish_mesh(bm, name, coll, material, loc, parent)


# ================================================================ 7. Gate (countertop POS terminal)
# The Counterfoil gate *is* the POS card terminal: the web page draws the live result

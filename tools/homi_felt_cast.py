"""The Return Crew as needle-felt 3D characters, modelled on Codex's sheets (docs/gorseller/karakterler/codex/,
material-notes.txt). Counterfoil first; Foil was the first style test.
Run: Blender -b --python tools/homi_felt_cast.py -- <character> [render]
  -> docs/gorseller/karakterler/homi-felt-cast.blend, <character>-v*.png
Each character is an empty 'Felt_<Name>' at its feet; pupils are separate ('<Name>_Pupil_L/R') so the web page can
turn them, and the body towards the pointer.
"""
import bpy, math, sys
from mathutils import Vector
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/gorseller/karakterler'


def srgb(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)


def felt(name, hexcol, fuzz=1.0):
    """Felt: matte, strong sheen, fine fibre bump."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = (*srgb(hexcol), 1)
    b.inputs['Roughness'].default_value = 0.95
    b.inputs['Sheen Weight'].default_value = 1.0 * fuzz
    b.inputs['Sheen Roughness'].default_value = 0.35
    b.inputs['Sheen Tint'].default_value = (1, 1, 1, 1)
    b.inputs['Subsurface Weight'].default_value = 0.08
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 420
    noise.inputs['Detail'].default_value = 8
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.35 * fuzz
    bump.inputs['Distance'].default_value = 0.002
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    m.diffuse_color = (*srgb(hexcol), 1)
    return m


def glossy(name, hexcol, rough=0.15):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*srgb(hexcol), 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = 0.6
    m.diffuse_color = (*srgb(hexcol), 1)
    return m


def link(o, col):
    for c in o.users_collection:
        c.objects.unlink(o)
    col.objects.link(o)
    return o


def sphere(name, loc, scale, mat, col, parent=None, seg=48):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    o.parent = parent
    return link(o, col)


def rounded_box(name, loc, size, bevel, mat, col, parent=None):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    mod = o.modifiers.new('round', 'BEVEL')
    mod.width, mod.segments = bevel, 8
    sub = o.modifiers.new('soft', 'SUBSURF')
    sub.levels = sub.render_levels = 2
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    o.parent = parent
    return link(o, col)


def eye(prefix, side, head, col, x, z, r=0.13):
    white = glossy('Felt_EyeWhite', '#fbfaf6', 0.25)
    black = glossy('Felt_Pupil', '#1b1d22', 0.08)
    shine = bpy.data.materials.get('Felt_Shine') or bpy.data.materials.new('Felt_Shine')
    shine.use_nodes = True
    sb = next(n for n in shine.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    sb.inputs['Emission Color'].default_value = (1, 1, 1, 1)
    sb.inputs['Emission Strength'].default_value = 3
    e = sphere(f'{prefix}_Eye_{side}', (x, -0.60, z), (r, r * 0.6, r * 1.1), white, col, head)
    p = sphere(f'{prefix}_Pupil_{side}', (x, -0.66, z - 0.01), (r * 0.62, r * 0.35, r * 0.7), black, col, head)
    sphere(f'{prefix}_Shine_{side}', (x + 0.03, -0.73, z + 0.045), (0.028, 0.012, 0.028), shine, col, p)
    return e, p


def foil(col):
    """Foil: Counterfoil's gatekeeper. A round cream plush with a navy guard cap, a frown he can switch on, and a
    stamp with a green PASS face."""
    cream, navy, green, salmon, wood = (felt('Felt_Cream', '#f3e7d3'), felt('Felt_Navy', '#25395a'),
                                        felt('Felt_Green', '#3f8f6c'), felt('Felt_Blush', '#f1a08e', 0.6),
                                        felt('Felt_Wood', '#b98a5c', 0.5))
    root = bpy.data.objects.new('Felt_Foil', None)
    col.objects.link(root)
    body = sphere('Foil_Body', (0, 0, 0.62), (0.62, 0.55, 0.6), cream, col, root)
    head = bpy.data.objects.new('Foil_Head', None)            # pivot at the neck: turn this towards the pointer
    col.objects.link(head)
    head.parent = root
    head.location = (0, 0, 1.05)
    sphere('Foil_HeadBall', (0, 0, 0.42), (0.66, 0.6, 0.6), cream, col, head)
    cap = rounded_box('Foil_Cap', (0, 0.02, 0.92), (1.0, 0.95, 0.26), 0.12, navy, col, head)
    rounded_box('Foil_CapBrim', (0, -0.42, 0.8), (0.86, 0.36, 0.06), 0.03, navy, col, head)
    sphere('Foil_CapBadge', (0, -0.43, 0.94), (0.09, 0.03, 0.09), green, col, head)
    for side, x in (('L', -0.22), ('R', 0.22)):
        eye('Foil', side, head, col, x, 0.48)
        sphere(f'Foil_Cheek_{side}', (x * 1.55, -0.53, 0.3), (0.11, 0.04, 0.07), salmon, col, head)
        brow = rounded_box(f'Foil_Brow_{side}', (x, -0.6, 0.68), (0.2, 0.05, 0.05), 0.02, navy, col, head)
        brow.rotation_euler = (0, math.radians(-12 if side == 'L' else 12), 0)   # the serious look
    sphere('Foil_Nose', (0, -0.62, 0.36), (0.06, 0.04, 0.05), salmon, col, head)
    # arms and feet
    for side, x in (('L', -0.62), ('R', 0.62)):
        arm = sphere(f'Foil_Arm_{side}', (x, -0.05, 0.7), (0.16, 0.16, 0.3), cream, col, root)
        arm.rotation_euler = (math.radians(-35), math.radians(25 if side == 'L' else -25), 0)
        sphere(f'Foil_Foot_{side}', (x * 0.5, -0.12, 0.08), (0.2, 0.26, 0.11), navy, col, root)
    # the stamp in his right hand: wooden handle, green PASS face
    stamp = bpy.data.objects.new('Foil_Stamp', None)
    col.objects.link(stamp)
    stamp.parent = root
    stamp.location = (0.78, -0.42, 0.55)
    sphere('Foil_StampKnob', (0, 0, 0.32), (0.11, 0.11, 0.11), wood, col, stamp)
    rounded_box('Foil_StampHandle', (0, 0, 0.16), (0.09, 0.09, 0.26), 0.03, wood, col, stamp)
    rounded_box('Foil_StampBase', (0, 0, 0.0), (0.34, 0.24, 0.1), 0.03, green, col, stamp)
    return root


FIBRES = '--no-fibres' not in sys.argv


def fuzz(o, length=0.024, count=30000):
    """Short wool fibres standing off the surface: the needle-felt look (render only)."""
    if not FIBRES:
        return
    ps = o.modifiers.new('felt_fibres', 'PARTICLE_SYSTEM').particle_system.settings
    ps.type = 'HAIR'
    ps.count = count
    ps.hair_length = length
    ps.child_type = 'INTERPOLATED'
    ps.rendered_child_count = 6
    ps.child_length = 0.7
    ps.child_length_threshold = 0.4          # uneven lengths, like teased wool
    ps.roughness_1, ps.roughness_1_size = 0.6, 0.4
    ps.roughness_endpoint = 0.3
    ps.kink = 'CURL'; ps.kink_amplitude = 0.004; ps.kink_frequency = 2.0
    ps.root_radius, ps.tip_radius = 0.0016, 0.0002
    ps.material_slot = o.material_slots[0].name if o.material_slots else ''
    ps.display_percentage = 5


def fibre_felt(name, hexcol):
    """Needle felt: very matte, strong sheen, two scales of fibre bump; stays readable without the fibres too."""
    m = felt(name, hexcol, 1.0)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    bump = next(n for n in nt.nodes if n.type == 'BUMP')
    vor = nt.nodes.new('ShaderNodeTexVoronoi')
    vor.feature = 'DISTANCE_TO_EDGE'
    vor.inputs['Scale'].default_value = 160
    mix = nt.nodes.new('ShaderNodeMath'); mix.operation = 'ADD'
    noise = next(n for n in nt.nodes if n.type == 'TEX_NOISE')
    nt.links.new(noise.outputs['Fac'], mix.inputs[0])
    nt.links.new(vor.outputs['Distance'], mix.inputs[1])
    nt.links.new(mix.outputs['Value'], bump.inputs['Height'])
    bump.inputs['Strength'].default_value = 0.55
    # a little colour variation across the wool
    ramp = nt.nodes.new('ShaderNodeMixRGB'); ramp.blend_type = 'MULTIPLY'
    ramp.inputs['Fac'].default_value = 0.18
    ramp.inputs['Color1'].default_value = (*srgb(hexcol), 1)
    nt.links.new(noise.outputs['Color'], ramp.inputs['Color2'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    return m


def capsule(name, a, b, r, mat, col, parent=None):
    """A rounded limb from a to b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d.length, vertices=32, location=(a + b) / 2)
    o = bpy.context.object
    o.name = name
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    o.data.materials.append(mat)
    bev = o.modifiers.new('round', 'BEVEL'); bev.width, bev.segments = r * 0.95, 8
    sub = o.modifiers.new('soft', 'SUBSURF'); sub.levels = sub.render_levels = 2
    bpy.ops.object.shade_smooth()
    o.parent = parent
    return link(o, col)


def counterfoil(col):
    """Counterfoil (Codex's sheet): two joined receipt halves of sage felt with cream scalloped layers at the top and
    bottom, a dashed seam down the middle, felt eyes looking sideways, a raised right hand, a ledger in the left arm
    open at '$40 LEFT', short thick legs."""
    sage, cream, ledger = fibre_felt('Felt_Sage', '#A5AD7B'), fibre_felt('Felt_Receipt', '#E4D8BB'), felt('Felt_Ledger', '#895638', 0.6)
    white, black = felt('Felt_EyeCream', '#F2E7D4', 0.5), felt('Felt_Ink', '#211B17', 0.4)
    brow_m, blush, page = felt('Felt_Brow', '#B8641F', 0.5), felt('Felt_Blush', '#D99A86', 0.6), felt('Felt_Page', '#EFE6CF', 0.3)
    root = bpy.data.objects.new('Felt_Counterfoil', None)
    col.objects.link(root)
    W, D, Z0, Z1 = 1.08, 0.36, 0.52, 2.0             # the receipt: width, depth, bottom and top
    body = rounded_box('Counterfoil_Body', (0, 0, (Z0 + Z1) / 2), (W, D, Z1 - Z0), 0.08, sage, col, root)
    fuzz(body)
    # cream receipt layers, a touch wider, with scallops along the top and the bottom edge
    body.scale = (1, 1, 1)
    for tag, z, sign in (('Top', Z1, 1), ('Bottom', Z0, -1)):
        band = rounded_box(f'Counterfoil_{tag}Band', (0, 0, z), (W - 0.02, D - 0.1, 0.1), 0.03, cream, col, root)
        fuzz(band, 0.016, 8000)
        n = 7
        for i in range(n):
            x = -W / 2 + W * (i + 0.5) / n
            bpy.ops.mesh.primitive_cylinder_add(radius=W / n * 0.55, depth=D - 0.1, vertices=32,
                                                location=(x, 0, z + sign * 0.035), rotation=(math.pi / 2, 0, 0))
            sc = bpy.context.object
            sc.name = f'Counterfoil_{tag}Scallop{i}'
            sc.scale = (1, 0.62, 1)
            sc.data.materials.append(cream)
            bev = sc.modifiers.new('round', 'BEVEL'); bev.width, bev.segments = 0.02, 6
            bpy.ops.object.shade_smooth()
            sc.parent = root
            link(sc, col)
    # the seam where the two halves meet: a groove, black dashes and cream stitches, front and back
    for face_y in (-D / 2 - 0.004, D / 2 + 0.004):
        for k in range(14):
            z = Z0 + 0.12 + k * (Z1 - Z0 - 0.24) / 13
            if k % 2 == 0:
                rounded_box(f'Counterfoil_Dash{face_y > 0}{k}', (0, face_y, z), (0.016, 0.01, 0.07), 0.004, black, col, root)
            else:
                sphere(f'Counterfoil_Stitch{face_y > 0}{k}', (0, face_y, z), (0.012, 0.006, 0.016), cream, col, root, 12)
    # face, on the front (-Y)
    fy = -D / 2
    for side, x in (('L', -0.25), ('R', 0.25)):
        sphere(f'Counterfoil_Eye_{side}', (x, fy - 0.025, 1.58), (0.135, 0.05, 0.15), white, col, root)
        sphere(f'Counterfoil_Pupil_{side}', (x - 0.05, fy - 0.07, 1.585), (0.07, 0.025, 0.098), black, col, root)
        arc = bpy.data.curves.new(f'Counterfoil_BrowCurve_{side}', 'CURVE'); arc.dimensions = '3D'
        arc.bevel_depth, arc.bevel_resolution = 0.018, 4
        sp = arc.splines.new('BEZIER'); sp.bezier_points.add(2)
        for j, (dx, dz) in enumerate(((-0.12, -0.02), (0.0, 0.03), (0.12, -0.02))):
            pt = sp.bezier_points[j]
            pt.co = (x + dx, fy - 0.012, 1.80 + dz)
            pt.handle_left_type = pt.handle_right_type = 'AUTO'
        brow = bpy.data.objects.new(f'Counterfoil_Brow_{side}', arc)
        arc.materials.append(brow_m)
        brow.parent = root
        col.objects.link(brow)
        sphere(f'Counterfoil_Cheek_{side}', (x * 1.25, fy - 0.006, 1.38), (0.085, 0.012, 0.085), blush, col, root)
    mouth = bpy.data.curves.new('Counterfoil_MouthCurve', 'CURVE'); mouth.dimensions = '3D'
    mouth.bevel_depth, mouth.bevel_resolution = 0.012, 4
    sp = mouth.splines.new('BEZIER'); sp.bezier_points.add(2)
    for j, (dx, dz) in enumerate(((-0.07, 0.02), (0.0, -0.03), (0.07, 0.02))):
        pt = sp.bezier_points[j]; pt.co = (dx, fy - 0.012, 1.40 + dz); pt.handle_left_type = pt.handle_right_type = 'AUTO'
    mo = bpy.data.objects.new('Counterfoil_Mouth', mouth); mouth.materials.append(black); mo.parent = root; col.objects.link(mo)
    # arms: his right (viewer's left, -X) raised in a calm wave, his left holds the ledger against the chest
    capsule('Counterfoil_ArmRaised', (-0.52, -0.02, 1.15), (-0.8, -0.08, 1.5), 0.095, sage, col, root)
    sphere('Counterfoil_HandRaised', (-0.84, -0.09, 1.62), (0.12, 0.07, 0.13), sage, col, root)
    for i, dx in enumerate((-0.07, -0.025, 0.02, 0.06)):
        capsule(f'Counterfoil_Finger{i}', (-0.84 + dx, -0.09, 1.7), (-0.84 + dx * 1.3, -0.09, 1.79 - abs(dx) * 0.6), 0.032, sage, col, root)
    capsule('Counterfoil_Thumb', (-0.74, -0.1, 1.6), (-0.68, -0.12, 1.66), 0.026, sage, col, root)
    capsule('Counterfoil_ArmHolding', (0.52, -0.02, 1.15), (0.36, -0.3, 0.86), 0.095, sage, col, root)
    sphere('Counterfoil_HandHolding', (0.2, -0.38, 0.84), (0.13, 0.08, 0.09), sage, col, root)
    # the ledger: brown cover, two cream pages open in a shallow V, '$40 LEFT' on the right page
    book = bpy.data.objects.new('Counterfoil_Ledger', None); col.objects.link(book); book.parent = root
    book.location = (0.02, -0.34, 1.0); book.rotation_euler = (math.radians(-10), 0, 0); book.scale = (0.9, 0.9, 0.9)
    for side, sx in (('L', -1), ('R', 1)):
        cover = rounded_box(f'Counterfoil_Cover_{side}', (sx * 0.15, 0.012, 0), (0.31, 0.02, 0.42), 0.01, ledger, col, book)
        cover.rotation_euler = (0, 0, math.radians(10 * sx))
        pg = rounded_box(f'Counterfoil_Page_{side}', (sx * 0.145, -0.006, 0), (0.28, 0.02, 0.39), 0.008, page, col, book)
        pg.rotation_euler = (0, 0, math.radians(10 * sx))
    t = bpy.data.curves.new('Counterfoil_LedgerText', 'FONT'); t.body = '$40\nLEFT'; t.size = 0.085; t.align_x = 'CENTER'
    t.materials.append(black)
    to = bpy.data.objects.new('Counterfoil_LedgerText', t); to.parent = book; col.objects.link(to)
    to.location = (0.145, -0.03, 0.02); to.rotation_euler = (math.pi / 2, 0, math.radians(10))
    for k in range(6):
        ln = rounded_box(f'Counterfoil_Line{k}', (-0.145, -0.03, 0.13 - k * 0.05), (0.2, 0.004, 0.008), 0.002, black, col, book)
        ln.rotation_euler = (0, 0, math.radians(-10))
    # legs and feet
    for side, x in (('L', -0.22), ('R', 0.22)):
        capsule(f'Counterfoil_Leg_{side}', (x * 1.05, 0, 0.56), (x * 1.05, -0.02, 0.16), 0.16, sage, col, root)
        foot = sphere(f'Counterfoil_Foot_{side}', (x * 1.08, -0.07, 0.1), (0.2, 0.25, 0.11), sage, col, root)
        fuzz(foot, 0.008, 3000)
    return root


def stage(col):
    floor_m = felt('Felt_Floor', '#efe2cf', 0.4)
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
    fl = bpy.context.object
    fl.name = 'Stage_Floor'
    fl.data.materials.append(floor_m)
    link(fl, col)
    w = bpy.data.worlds.new('Felt_World')
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (*srgb('#f4e6d6'), 1)
    bg.inputs['Strength'].default_value = 0.9
    bpy.context.scene.world = w
    key = bpy.data.lights.new('Key', 'AREA'); key.energy = 900; key.size = 4
    ko = bpy.data.objects.new('Key', key); col.objects.link(ko); ko.location = (-3, -4, 5); ko.rotation_euler = (math.radians(50), 0, math.radians(-35))
    rim = bpy.data.lights.new('Rim', 'AREA'); rim.energy = 500; rim.size = 3
    ro = bpy.data.objects.new('Rim', rim); col.objects.link(ro); ro.location = (3, 3, 4); ro.rotation_euler = (math.radians(-50), 0, math.radians(145))
    cam = bpy.data.objects.new('Felt_Cam', bpy.data.cameras.new('Felt_Cam'))
    col.objects.link(cam)
    cam.location = (1.8, -6.4, 2.2)
    cam.rotation_euler = (Vector((0, 0, 1.2)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 70
    bpy.context.scene.camera = cam


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.ops.preferences.addon_enable(module='cycles')
    except Exception as e:
        print('[FELT] cycles not available', e)
    sc = bpy.context.scene
    col = bpy.data.collections.new('HOMI_Felt_Cast')
    sc.collection.children.link(col)
    who = next((a for a in sys.argv[sys.argv.index('--') + 1:] if not a.startswith('-') and a != 'render'), 'counterfoil') if '--' in sys.argv else 'counterfoil'
    {'foil': foil, 'counterfoil': counterfoil}[who](col)
    stage(col)
    try:                                        # the engine enum under-reports add-on engines; just try Cycles
        sc.render.engine = 'CYCLES'
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'NONE' if '--cpu' in sys.argv else 'METAL'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
    except (TypeError, KeyError) as e:
        print('[FELT] Cycles unavailable:', e)
    print('[FELT] engine', sc.render.engine, 'fibres', FIBRES)
    if sc.render.engine == 'CYCLES':
        sc.cycles.samples = 128
        sc.cycles.device = 'CPU' if '--cpu' in sys.argv else 'GPU'
        sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1080
    sc.view_settings.view_transform = 'AgX'
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'homi-felt-cast.blend'))
    if 'render' in sys.argv:
        n = 1
        while (OUT / f'{who}-v{n}.png').exists():
            n += 1
        sc.render.filepath = str(OUT / f'{who}-v{n}.png')
        bpy.ops.render.render(write_still=True)


main()

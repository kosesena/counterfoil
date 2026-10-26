"""Counterfoil (the approved plum design, docs/gorseller/karakterler/codex/counterfoil-approved/00-character.png) as a
needle-felt 3D figure for the Overview hero, where he turns towards the pointer.
Run: blender -b --python tools/counterfoil_claude_3d.py -- [render] [--fibres]
  -> docs/gorseller/karakterler/counterfoil-claude-3d.blend (+ counterfoil-claude-3d-v*.png with 'render')
Rig for the web (tools/export_counterfoil_glb.py): 'Counterfoil' at the feet; 'CF_Upper' (body, beret, brows, moustache,
arms) pivots above the legs; 'CF_Eyes' sits in the middle of the body, so turning it slides both bead eyes over the face.
"""
import bpy, bmesh, math, sys
from mathutils import Vector, noise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/gorseller/karakterler'
FIBRES = '--fibres' in sys.argv              # hair particles: off by default, the web cannot show them

BODY_C, BODY_R = Vector((0, 0, 0.96)), Vector((0.42, 0.38, 0.56))   # the egg: centre and half-sizes


def srgb(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)


def felt(name, hexcol, fuzz=1.0):
    """Felt: matte, strong sheen, fine fibre bump (same recipe as homi_felt_cast.py)."""
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
    noise_n = nt.nodes.new('ShaderNodeTexNoise')
    noise_n.inputs['Scale'].default_value = 260
    noise_n.inputs['Detail'].default_value = 8
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.7 * fuzz
    bump.inputs['Distance'].default_value = 0.002
    nt.links.new(noise_n.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])
    m.diffuse_color = (*srgb(hexcol), 1)
    return m


def bead(name, hexcol):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*srgb(hexcol), 1)
    b.inputs['Roughness'].default_value = 0.06
    b.inputs['Coat Weight'].default_value = 0.5
    m.diffuse_color = (*srgb(hexcol), 1)
    return m


def place(o, col, parent, mat=None, local=False):
    """Link into the collection and parent; positions are world unless local (then relative to the parent)."""
    for c in o.users_collection:
        c.objects.unlink(o)
    col.objects.link(o)
    if mat and not o.data.materials:
        o.data.materials.append(mat)
    if parent:
        o.parent = parent
        if not local:
            o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o


def lumpy(o, amp, scale):
    """Hand-felted surfaces are never quite round: push each vertex along its normal by a soft noise."""
    me = o.data
    for v in me.vertices:
        p = o.matrix_world @ v.co
        v.co += v.normal * amp * noise.noise(p * scale)


def sphere(name, loc, scale, mat, col, parent=None, seg=40, rot=(0, 0, 0), local=False):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.shade_smooth()
    return place(o, col, parent, mat, local)


def tube(name, pts, r, mat, col, parent=None, radii=None, local=False):
    """A felt rope along a smooth curve; radii taper it (moustache, arms, brows)."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth, cu.bevel_resolution, cu.resolution_u = r, 5, 10
    cu.use_fill_caps = True
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        bp = sp.bezier_points[i]
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
        bp.radius = radii[i] if radii else 1.0
    o = bpy.data.objects.new(name, cu)
    cu.materials.append(mat)
    bpy.context.scene.collection.objects.link(o)
    return place(o, col, parent, local=local)


def fuzz(o, length=0.012, count=20000):
    """Short wool fibres standing off the surface: render only, the web gets sheen instead."""
    if not FIBRES:
        return
    ps = o.modifiers.new('felt_fibres', 'PARTICLE_SYSTEM').particle_system.settings
    ps.type = 'HAIR'
    ps.count = count
    ps.hair_length = length
    ps.child_type = 'INTERPOLATED'
    ps.rendered_child_count = 5
    ps.child_length = 0.7
    ps.child_length_threshold = 0.4
    ps.roughness_1, ps.roughness_1_size = 0.6, 0.4
    ps.kink = 'CURL'; ps.kink_amplitude = 0.003; ps.kink_frequency = 2.0
    ps.root_radius, ps.tip_radius = 0.0012, 0.0002
    ps.display_percentage = 5


def surface_y(body, x, z):
    """Where the front of the egg is at (x, z): cast a ray from in front."""
    hit, loc, *_ = body.ray_cast(Vector((x, -2, z)), Vector((0, 1, 0)))
    return loc.y if hit else -BODY_R.y


def counterfoil(col):
    plum, rust, cream = felt('Felt_Plum', '#5E1F56'), felt('Felt_Rust', '#7C2014'), felt('Felt_Cream', '#E8D3AE', 0.8)
    lilac, black = felt('Felt_Lilac', '#C3A6E4', 0.8), bead('Bead_Black', '#0B0A0C')

    root = bpy.data.objects.new('Counterfoil', None)
    col.objects.link(root)
    upper = bpy.data.objects.new('CF_Upper', None)
    col.objects.link(upper)
    upper.location = (0, 0, 0.42)
    upper.parent = root
    bpy.context.view_layer.update()

    # the egg: a sphere, a touch fuller at the bottom, lumpy like pressed wool
    bpy.ops.mesh.primitive_uv_sphere_add(segments=72, ring_count=40, radius=1)
    body = bpy.context.object
    body.name = 'CF_Body'
    for v in body.data.vertices:
        f = 1 + 0.09 * -v.co.z
        v.co = Vector((v.co.x * BODY_R.x * f, v.co.y * BODY_R.y * f, v.co.z * BODY_R.z)) + BODY_C
    body.data.update()
    lumpy(body, 0.012, 5.0)
    bpy.ops.object.shade_smooth()
    place(body, col, upper, plum)
    fuzz(body, 0.012, 40000)
    bpy.context.view_layer.update()

    # bead eyes on a pivot in the middle of the egg: turning it rolls them across the face
    eyes = bpy.data.objects.new('CF_Eyes', None)
    col.objects.link(eyes)
    eyes.location = BODY_C + Vector((0, 0.05, 0.12))
    eyes.parent = upper
    eyes.matrix_parent_inverse = upper.matrix_world.inverted()
    bpy.context.view_layer.update()
    for side, x in (('L', -0.105), ('R', 0.105)):
        z = 1.10
        y = surface_y(body, x, z)
        sphere(f'CF_Eye_{side}', (x, y + 0.012, z), (0.06, 0.05, 0.064), black, col, eyes, 32)
        # brows: thick lilac sausages, inner ends lower, the stern look of the sheet
        sx = 1 if x > 0 else -1
        bz = [(0.05, 1.215), (0.14, 1.255), (0.24, 1.235)]
        pts = [(sx * bx, surface_y(body, sx * bx, b) - 0.015, b) for bx, b in bz]
        tube(f'CF_Brow_{side}', pts, 0.042, lilac, col, upper, radii=[0.75, 1.0, 0.7])

    # the handlebar moustache: two cream ropes from under the eyes, sweeping out past the body and curling up
    half = [(-0.04, 0.975, 0.85), (0.13, 0.95, 1.2), (0.30, 0.88, 1.15), (0.47, 0.83, 0.95),
            (0.63, 0.86, 0.66), (0.71, 0.97, 0.46), (0.67, 1.07, 0.34), (0.59, 1.05, 0.26), (0.60, 0.99, 0.18)]
    for side, sx in (('L', -1), ('R', 1)):
        pts, radii = [], []
        for x, z, r in half:
            y = surface_y(body, sx * x, z) - 0.04 if x < 0.36 else -0.30 + (x - 0.36) * 0.25
            pts.append((sx * x, y, z))
            radii.append(r)
        tube(f'CF_Moustache_{side}', pts, 0.1, cream, col, upper, radii=radii)

    # beret: a soft disc tipped down to his right (the viewer's left), a rolled rim and a little stalk
    beret = bpy.data.objects.new('CF_Beret', None)
    col.objects.link(beret)
    beret.location = (-0.06, 0.02, 1.44)
    beret.rotation_euler = (math.radians(-8), math.radians(-18), 0)
    beret.parent = upper
    beret.matrix_parent_inverse = upper.matrix_world.inverted()
    bpy.context.view_layer.update()
    top = sphere('CF_BeretTop', (0, 0, 0.03), (0.50, 0.47, 0.14), rust, col, beret, 56, local=True)
    lumpy(top, 0.01, 8)
    fuzz(top, 0.01, 12000)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.36, minor_radius=0.065, major_segments=64, minor_segments=20,
                                     location=(0, 0, -0.04))
    rim = bpy.context.object
    rim.name = 'CF_BeretRim'
    bpy.ops.object.shade_smooth()
    place(rim, col, beret, rust, local=True)
    tube('CF_BeretStalk', [(0.0, 0, 0.13), (0.02, 0, 0.21), (0.08, 0, 0.24)], 0.035, rust, col, beret, local=True)

    # arms: his right hand on the hip, his left up at the moustache, fingers curled round it
    tube('CF_Arm_Hip', [(-0.36, 0.02, 0.84), (-0.50, 0.0, 0.76), (-0.53, -0.02, 0.63), (-0.42, -0.06, 0.57)],
         0.06, plum, col, upper, radii=[1.0, 1.0, 0.95, 0.9])
    sphere('CF_Hand_Hip', (-0.41, -0.07, 0.575), (0.07, 0.06, 0.06), plum, col, upper)
    tube('CF_Arm_Twirl', [(0.36, -0.10, 0.74), (0.50, -0.22, 0.66), (0.58, -0.30, 0.72), (0.56, -0.33, 0.80)],
         0.06, plum, col, upper, radii=[1.0, 1.0, 0.95, 0.9])
    sphere('CF_Hand_Twirl', (0.55, -0.34, 0.86), (0.08, 0.07, 0.085), plum, col, upper)
    for i, (dz, dx) in enumerate(((0.06, -0.03), (0.02, -0.05), (-0.02, -0.04))):
        sphere(f'CF_Finger{i}', (0.55 + dx, -0.40, 0.84 + dz), (0.035, 0.035, 0.03), plum, col, upper, 20)
    sphere('CF_Thumb', (0.61, -0.36, 0.88), (0.03, 0.03, 0.045), plum, col, upper, 20)

    # legs and the rust slippers stay put; only the upper half turns
    for side, x in (('L', -0.14), ('R', 0.14)):
        tube(f'CF_Leg_{side}', [(x, 0, 0.48), (x * 1.02, -0.01, 0.30), (x * 1.08, -0.02, 0.15)], 0.055, plum, col, root)
        shoe = sphere(f'CF_Shoe_{side}', (x * 1.3, -0.09, 0.10), (0.19, 0.25, 0.10), rust, col, root)
        lumpy(shoe, 0.006, 12)
        fuzz(shoe, 0.008, 6000)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.08, minor_radius=0.05, major_segments=40, minor_segments=16,
                                         location=(x * 1.12, -0.04, 0.21))
        cuff = bpy.context.object
        cuff.name = f'CF_Cuff_{side}'
        bpy.ops.object.shade_smooth()
        place(cuff, col, root, rust)
    return root


def stage(col):
    floor_m = felt('Felt_Floor', '#F3EADF', 0.3)
    bpy.ops.mesh.primitive_plane_add(size=30)
    fl = bpy.context.object
    fl.name = 'Stage_Floor'
    place(fl, col, None, floor_m)
    w = bpy.data.worlds.new('Felt_World')
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (*srgb('#F6EEE4'), 1)
    bg.inputs['Strength'].default_value = 0.9
    bpy.context.scene.world = w
    for name, e, s, loc, rot in (('Key', 260, 3, (-2.4, -3.6, 3.4), (52, 0, -34)), ('Rim', 160, 2.5, (2.6, 2.6, 3.0), (-50, 0, 140))):
        li = bpy.data.lights.new(name, 'AREA'); li.energy = e; li.size = s
        lo = bpy.data.objects.new(name, li); col.objects.link(lo)
        lo.location = loc; lo.rotation_euler = [math.radians(a) for a in rot]
    cam = bpy.data.objects.new('CF_Cam', bpy.data.cameras.new('CF_Cam'))
    col.objects.link(cam)
    cam.location = (0.9, -5.6, 1.35)
    cam.rotation_euler = (Vector((0, 0, 0.82)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 62
    bpy.context.scene.camera = cam


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    col = bpy.data.collections.new('Counterfoil_3D')
    sc.collection.children.link(col)
    counterfoil(col)
    stage(col)
    try:
        sc.render.engine = 'CYCLES'
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        sc.cycles.device = 'GPU'
        sc.cycles.samples = 96
        sc.cycles.use_denoising = True
    except (TypeError, KeyError) as e:
        print('[CF] Cycles unavailable:', e)
    sc.render.resolution_x, sc.render.resolution_y = 900, 1100
    sc.view_settings.view_transform = 'AgX'
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'counterfoil-claude-3d.blend'))
    if 'render' in sys.argv:
        n = 1
        while (OUT / f'counterfoil-claude-3d-v{n}.png').exists():
            n += 1
        sc.render.filepath = str(OUT / f'counterfoil-claude-3d-v{n}.png')
        bpy.ops.render.render(write_still=True)


main()

"""Rigid cast rigs for Blender 5.2. Run on the already opened source .blend.

Only generated rigs/actions are replaced. Original instance animation, geometry,
modifiers and collection memberships are preserved. Run with Blender -b ...
--python tools/rig_and_animate.py. Successful execution saves the current file.
"""
import math
import re
import bpy
from mathutils import Matrix, Quaternion, Vector

ROLES = ('Customer', 'Store_Manager', 'Reader_Agent', 'Transaction_Agent')
TAG = 'cf_rigid_rig_v1'
REST = 'cf_rigid_rest_world_v1'
START, END = 1, 720
WALK_END = 590   # customer reaches the till (Inst_Customer's last location key)
TAU = 2.0 * math.pi


def log(message):
    print('[rig_and_animate] ' + message, flush=True)


def curves(action, slot=None):
    """Read layered actions without relying on the removed action.fcurves API."""
    if action is None:
        return
    layers = getattr(action, 'layers', ())
    if layers:
        for layer in layers:
            for strip in layer.strips:
                for bag in getattr(strip, 'channelbags', ()):
                    if slot is None or bag.slot_handle == slot.handle:
                        yield from bag.fcurves
    else:
        yield from getattr(action, 'fcurves', ())


def motion_speeds():
    obj = bpy.data.objects.get('Inst_Customer')
    ad = obj.animation_data if obj else None
    loc = list(curves(ad.action, getattr(ad, 'action_slot', None))) if ad else []
    loc = [fc for fc in loc if fc.data_path == 'location' and not fc.mute]
    if not loc:
        log('Inst_Customer location curves unavailable; using timing fallback.')
        return None
    if ad.nla_tracks or ad.drivers:
        log('WARNING: speed sampling uses active location action, not NLA/drivers.')
    def point(frame):
        v = obj.location.copy()
        for fc in loc:
            v[fc.array_index] = fc.evaluate(frame)
        return v
    speeds = {f: (point(min(END, f + .5)) - point(max(START, f - .5))).length
              for f in range(START, END + 1)}
    moving = sorted(s for f, s in speeds.items() if (f < 50 or 80 < f < 170) and s > 1e-7)
    if not moving:
        log('No usable translation speed; using timing fallback.')
        return None
    reference = moving[len(moving) // 2]
    return {f: min(1.15, s / reference) for f, s in speeds.items()}


def part_name(obj, role):
    return re.sub(r'\.\d{3}$', '', obj.name[len(role) + 1:])


def bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return (Vector(tuple(min(p[i] for p in points) for i in range(3))),
            Vector(tuple(max(p[i] for p in points) for i in range(3))))


def center(obj):
    low, high = bounds(obj)
    return (low + high) * .5


def top(obj):
    low, high = bounds(obj)
    v = (low + high) * .5
    v.z = high.z
    return v


def restore_parts(parts, root):
    for obj in parts:
        if REST not in obj:
            if obj.parent and obj.parent.type == 'ARMATURE':
                raise RuntimeError('Foreign rig without stored rest transform: ' + obj.name)
            obj[REST] = [value for row in obj.matrix_world for value in row]
        values = list(obj[REST])
        world = Matrix([values[i:i + 4] for i in range(0, 16, 4)])
        obj.parent = root
        obj.parent_type = 'OBJECT'
        obj.parent_bone = ''
        obj.matrix_parent_inverse = root.matrix_world.inverted()
        obj.matrix_world = world


def cleanup():
    for obj in list(bpy.data.objects):
        if obj.type == 'ARMATURE' and obj.get(TAG):
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data.users == 0:
                bpy.data.armatures.remove(data)
    for action in list(bpy.data.actions):
        if action.get(TAG) and action.users == 0:
            bpy.data.actions.remove(action)


def destination(name):
    """Accessories not recognized explicitly follow the torso and are logged."""
    lower = name.lower()
    side = 'L' if '-1' in name or name.endswith('.L') else 'R'
    if lower.startswith(('arm', 'hand')):
        return 'upper_arm.' + side
    if lower.startswith(('leg', 'shoe', 'foot')):
        return 'leg.' + side
    if lower.startswith(('head', 'ear', 'eye', 'brow', 'nose', 'smile', 'mouth',
                         'fringe', 'hair', 'glasses', 'glass', 'spectacle',
                         'lens', 'pupil', 'beard', 'mustache', 'eyeglass')):
        return 'head'
    return 'spine'


def build_rig(role, root, parts, stage):
    names = {part_name(o, role): o for o in parts}
    required = ('Torso', 'Neck', 'Head', 'Arm-1', 'Arm1', 'Leg-1', 'Leg1')
    missing = [name for name in required if name not in names]
    if missing:
        raise RuntimeError(role + ': missing parts: ' + ', '.join(missing))
    hips = (top(names['Leg-1']) + top(names['Leg1'])) * .5
    neck = top(names['Neck'])
    torso = center(names['Torso'])
    stature = max(bounds(o)[1].z for o in parts) - min(bounds(o)[0].z for o in parts)
    length = max(.01, stature * .08)
    data = bpy.data.armatures.new('CF_Rig_' + role)
    rig = bpy.data.objects.new('CF_Rig_' + role, data)
    rig[TAG] = True
    data[TAG] = True
    # Include every collection containing the role, including aggregate casts.
    collections = set(root.users_collection)
    for obj in parts:
        collections.update(obj.users_collection)
    for name in ('Cast_' + role, 'Counterfoil_Cast', 'Counterfoil_Cast_NoTitle'):
        collection = bpy.data.collections.get(name)
        if collection and any(o == root or o in parts for o in collection.all_objects):
            collections.add(collection)
    for collection in collections:
        if rig.name not in collection.objects:
            collection.objects.link(rig)
    if rig.name not in stage.collection.objects:
        stage.collection.objects.link(rig)
    rig.parent = root
    rig.matrix_parent_inverse = root.matrix_world.inverted()
    rig.matrix_world = Matrix.Identity(4)
    rig.show_in_front = True
    stage.view_layers[0].objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    def bone(name, pivot, parent=None, size=length):
        b = data.edit_bones.new(name)
        b.head = pivot
        b.tail = pivot + Vector((0, 0, size))
        b.use_deform = False
        if parent:
            b.parent = data.edit_bones[parent]
        b.use_connect = False
    bone('root', Vector((hips.x, hips.y, min(bounds(o)[0].z for o in parts))))
    bone('hips', hips, 'root')
    bone('spine', hips, 'hips', max(length, torso.z - hips.z))
    bone('neck', neck, 'spine')
    bone('head', neck, 'neck', max(length, top(names['Head']).z - neck.z))
    for side, suffix in (('L', '-1'), ('R', '1')):
        bone('upper_arm.' + side, top(names['Arm' + suffix]), 'spine')
        bone('leg.' + side, top(names['Leg' + suffix]), 'hips')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()
    for obj in parts:
        name = part_name(obj, role)
        target = destination(name)
        if role == 'Customer' and name in ('ShoppingBag', 'BagHandle'):
            target = 'upper_arm.R'
        # Catch unnamed glasses frames by their position in the head region.
        if target == 'spine' and name not in ('Torso', 'Neck', 'ShoppingBag', 'BagHandle'):
            if center(obj).z >= neck.z:
                target = 'head'
            log(f'{obj.name}: accessory -> {target}')
        world = obj.matrix_world.copy()
        obj.parent = rig
        obj.parent_type = 'BONE'
        obj.parent_bone = target
        # Object bone parenting uses the bone tail as origin by default.
        pb = rig.pose.bones[target]
        parent_world = rig.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.bone.length, 0))
        if hasattr(obj, 'parent_bone_head_tail_factor'):
            obj.parent_bone_head_tail_factor = 1.0
        obj.matrix_parent_inverse = parent_world.inverted()
        obj.matrix_basis = world
    bpy.context.view_layer.update()
    for obj in parts:
        expected = list(obj[REST])
        error = max(abs(obj.matrix_world[i][j] - expected[i * 4 + j])
                    for i in range(4) for j in range(4))
        if error > 1e-4:
            raise RuntimeError(f'Bone-parent changed rest transform: {obj.name} ({error})')
    rig.select_set(False)
    log(f'{role}: {len(parts)} rigid parts, collections: ' + ', '.join(sorted(c.name for c in collections if c != stage.collection)))
    return rig


def smooth(a, b, value):
    t = max(0.0, min(1.0, (value - a) / (b - a)))
    return t * t * (3 - 2 * t)


def window(frame, start, stop, fade=6):
    return smooth(start, start + fade, frame) * (1 - smooth(stop - fade, stop, frame))


def rotate(pb, x=0, y=0, z=0):
    basis = pb.bone.matrix_local.to_quaternion().inverted()
    q = Quaternion()
    for axis, angle in (((1, 0, 0), x), ((0, 1, 0), y), ((0, 0, 1), z)):
        q = q @ Quaternion(basis @ Vector(axis), math.radians(angle))
    pb.rotation_quaternion = q


def animate(rig, role, speeds):
    bones = rig.pose.bones
    for pb in bones:
        pb.rotation_mode = 'QUATERNION'
    phase = ROLES.index(role) * 1.7
    step = 0.0
    # Exact 240-frame periodic idle: endpoint at 241 repeats frame 1.
    for f in range(START, END + 2):
        t = f - 1
        cycle = TAU * t / 240
        # Three full breaths per loop (~3.33 s at 24 fps).
        breath = math.sin(3 * cycle + phase)
        for pb in bones:
            pb.location = (0, 0, 0)
            pb.scale = (1, 1, 1)
            pb.rotation_quaternion = Quaternion()
        bones['spine'].scale = (1 + .003 * breath, 1 + .006 * breath, 1 + .003 * breath)
        rotate(bones['head'], z=12 * math.sin(cycle + phase))
        if role == 'Customer':
            envelope = max(window(f, 0, 50, 5), window(f, 80, WALK_END, 8))
            speed = speeds.get(min(f, END), 0) if speeds else 1.0
            strength = envelope * min(1, speed)
            step += TAU / 18 * min(1.25, max(0, speed))
            swing = math.sin(step)
            push = window(f, 76, WALK_END - 4, 6)
            pay = window(f, WALK_END + 22, WALK_END + 100, 10)   # holds the card to the till terminal
            for side, sign in (('L', 1), ('R', -1)):
                rotate(bones['leg.' + side], x=sign * 25 * swing * strength)
                rotate(bones['upper_arm.' + side],
                       x=-70 * push - sign * 18 * swing * strength * (1 - push) - (55 * pay if side == 'R' else 0))
            # With a hanging limb along -Z, negative world-X points toward -Y.
            offset = .02 * strength * (.5 - .5 * math.cos(2 * step))
            bones['hips'].location = bones['hips'].bone.matrix_local.to_quaternion().inverted() @ Vector((0, 0, offset))
        else:
            gesture = max(0.0, math.sin(cycle + phase)) ** 4
            if role == 'Reader_Agent':
                rotate(bones['upper_arm.R'], x=-62 * gesture, y=-10 * gesture)
                rotate(bones['head'], x=14 * gesture, z=12 * math.sin(cycle + phase) * (1 - .65 * gesture))
            elif role == 'Transaction_Agent':
                rotate(bones['upper_arm.L'], x=-32 * gesture, y=-8 * gesture)
            else:   # Store_Manager: reads approvals on the tablet in her right hand
                rotate(bones['head'], x=16 + 6 * gesture, z=6 * math.sin(cycle + phase))
                rotate(bones['upper_arm.R'], x=-55 - 4 * gesture)
        for pb in bones:
            pb.keyframe_insert(data_path='rotation_quaternion', frame=f, group=pb.name)
        bones['spine'].keyframe_insert(data_path='scale', frame=f, group='spine')
        bones['hips'].keyframe_insert(data_path='location', frame=f, group='hips')
    action = rig.animation_data.action
    action.name = 'CF_Animation_' + role
    action[TAG] = True
    for fc in curves(action, rig.animation_data.action_slot):
        for point in fc.keyframe_points:
            point.interpolation = 'LINEAR'
        if role != 'Customer':
            fc.modifiers.new('CYCLES')


def main():
    if not bpy.data.filepath:
        raise RuntimeError('Open the intended .blend first; no output path is guessed.')
    original_scene = bpy.context.scene
    original_frame = original_scene.frame_current
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    speeds = motion_speeds()
    cast = []
    for role in ROLES:
        root = bpy.data.objects.get('CF_' + role)
        if root is None or root.type != 'EMPTY':
            raise RuntimeError('Missing EMPTY root: CF_' + role)
        parts = [o for o in bpy.data.objects if o.type in {'MESH', 'CURVE'}
                 and o.name.startswith(role + '_')]
        if not parts:
            raise RuntimeError('No parts found: ' + role)
        cast.append((role, root, parts))
    # A temporary scene makes excluded/source-only collections editable headlessly.
    stage = bpy.data.scenes.new('__CF_Rig_Work__')
    window_context = bpy.context.window
    if window_context is None:
        bpy.data.scenes.remove(stage)
        raise RuntimeError('A Blender window context is required (also supplied by -b).')
    try:
        window_context.scene = stage
        for _, root, parts in cast:
            for obj in [root] + parts:
                if obj.name not in stage.collection.objects:
                    stage.collection.objects.link(obj)
        bpy.context.view_layer.update()
        for _, root, parts in cast:
            restore_parts(parts, root)
        cleanup()
        bpy.context.view_layer.update()
        rigs = [(role, build_rig(role, root, parts, stage)) for role, root, parts in cast]
        for role, rig in rigs:
            animate(rig, role, speeds)
        for scene in bpy.data.scenes:
            if scene != stage:
                scene.frame_start, scene.frame_end = START, END
                scene.render.fps = 24
                scene.render.fps_base = 1.0
    finally:
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        window_context.scene = original_scene
        bpy.data.scenes.remove(stage)
        original_scene.frame_set(original_frame)
    log('Rigging and animation complete; saving current blend.')
    bpy.ops.wm.save_mainfile(compress=True)


if __name__ == '__main__':
    main()

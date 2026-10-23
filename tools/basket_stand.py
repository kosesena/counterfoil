"""Replace the entrance basket stand in Blender 5.2; save the opened .blend.

Run: Blender -b docs/gorseller/counterfoil-magaza.blend --python tools/basket_stand.py
Geometry and materials owned by this script use SE_BStand_ for repeatable rebuilds.
All dimensions are metres; placement is checked against evaluated world bounds.
"""
import math
import re
import bpy
from mathutils import Vector

PREFIX = 'SE_BStand_'
SCENE = 'Counterfoil_Market_Composite'
COLLECTION = 'Kat 1 · Market'
OLD = {f'SE_Basket_{i}' for i in range(6)} | {
    'SE_BasketHandle-1', 'SE_BasketHandle1', 'SE_BasketPole', 'SE_BasketSign',
    'SE_BasketSignText', 'SE_BasketSignText_Back',
}


def log(message):
    print('[basket_stand] ' + message, flush=True)


def cleanup():
    for obj in list(bpy.data.objects):
        if obj.name in OLD or obj.name.startswith(PREFIX):
            bpy.data.objects.remove(obj, do_unlink=True)
    for blocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
        for block in list(blocks):
            if block.name.startswith(PREFIX) and block.users == 0:
                blocks.remove(block)


def material(name, color, roughness=.45, metallic=0):
    mat = bpy.data.materials.new(PREFIX + name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    if metallic:
        shader.inputs['Anisotropic'].default_value = .3
    return mat


def attach(name, data, collection, root, mat=None):
    obj = bpy.data.objects.new(PREFIX + name, data)
    collection.objects.link(obj)
    obj.parent = root
    if mat:
        data.materials.append(mat)
    return obj


def mesh(name, vertices, faces, collection, root, mat, bevel=0):
    data = bpy.data.meshes.new(PREFIX + name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = attach(name, data, collection, root, mat)
    if bevel:
        mod = obj.modifiers.new(PREFIX + 'SoftEdges', 'BEVEL')
        mod.width, mod.segments = bevel, 3
    return obj


def box(name, center, size, collection, root, mat, bevel=.004):
    x, y, z = (v / 2 for v in size)
    vertices = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
                (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    faces = [(3, 2, 1, 0), (0, 1, 5, 4), (1, 2, 6, 5),
             (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)]
    obj = mesh(name, vertices, faces, collection, root, mat, bevel)
    obj.location = center
    return obj


def tube(name, points, radius, collection, root, mat, closed=False):
    data = bpy.data.curves.new(PREFIX + name, 'CURVE')
    data.dimensions = '3D'
    data.bevel_depth, data.bevel_resolution = radius, 3
    data.use_fill_caps = True
    spline = data.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for point, xyz in zip(spline.points, points):
        point.co = (*xyz, 1)
    spline.use_cyclic_u = closed
    return attach(name, data, collection, root, mat)


def rounded_rectangle(x, y, radius, z):
    points = []
    for cx, cy, start in ((x-radius, y-radius, 0), (-x+radius, y-radius, 90),
                          (-x+radius, -y+radius, 180), (x-radius, -y+radius, 270)):
        for step in range(9):
            angle = math.radians(start + step * 90 / 8)
            points.append((cx + radius * math.cos(angle),
                           cy + radius * math.sin(angle), z))
    return points


def basket(index, collection, root, red, steel, rubber):
    name = f'Basket{index:02d}'
    offset = Vector((.002 * (-1) ** index, 0, .145 + .075 * index))
    vertices, faces = [], []

    def quad(points):
        first = len(vertices)
        vertices.extend(points)
        faces.append(tuple(range(first, first + 4)))

    def ring(z):
        x, y = .165 + .05 * z / .22, .10 + .05 * z / .22
        return [Vector((-x, -y, z)), Vector((x, -y, z)),
                Vector((x, y, z)), Vector((-x, y, z))]

    # Open horizontal slots between bands; narrow upright webs tie them together.
    quad(list(reversed(ring(0))))
    for low, high in ((0, .018), (.039, .052), (.073, .086),
                      (.107, .120), (.141, .154), (.175, .188), (.207, .22)):
        a, b = ring(low), ring(high)
        for side in range(4):
            nxt = (side + 1) % 4
            quad([a[side], a[nxt], b[nxt], b[side]])
    bottom, top = ring(0), ring(.22)
    for side in range(4):
        nxt = (side + 1) % 4
        length = (top[nxt] - top[side]).length
        for fraction in (0, .25, .5, .75, 1):
            lo = max(0, fraction - .003 / length)
            hi = min(1, fraction + .003 / length)
            quad([bottom[side].lerp(bottom[nxt], lo), bottom[side].lerp(bottom[nxt], hi),
                  top[side].lerp(top[nxt], hi), top[side].lerp(top[nxt], lo)])
    obj = mesh(name + '_Shell', vertices, faces, collection, root, red)
    obj.location = offset
    solid = obj.modifiers.new(PREFIX + 'PlasticThickness', 'SOLIDIFY')
    solid.thickness, solid.offset = .0028, -1
    solid.use_even_offset = True
    bevel = obj.modifiers.new(PREFIX + 'MouldedEdges', 'BEVEL')
    bevel.width, bevel.segments = .0007, 2
    rim = rounded_rectangle(.215, .15, .025, .22)
    tube(name + '_RolledRim', [Vector(p) + offset for p in rim], .005,
         collection, root, red, True)
    for side in (-1, 1):
        # Two half-rings hinged at the short ends, folded into the rim plane.
        points = [( .205 * math.cos(t * math.pi / 48),
                   side * .145 * math.sin(t * math.pi / 48), .227) for t in range(49)]
        points = [Vector(p) + offset for p in points]
        tube(name + f'_Handle{side}', points, .0028, collection, root, steel)
        tube(name + f'_Grip{side}', points[19:30], .006, collection, root, rubber)
    for side in (-1, 1):
        box(name + f'_Hinge{side}', offset + Vector((side * .205, 0, .22)),
            (.018, .026, .014), collection, root, red, .003)


def dolly(collection, root, dark, steel, rubber):
    box('Dolly', (0, 0, .115), (.49, .36, .045), collection, root, dark, .015)
    for i, (x, y) in enumerate(((-.19, -.125), (.19, -.125),
                                (-.19, .125), (.19, .125))):
        tube(f'Castor{i}_Swivel', [(x, y, .068), (x, y, .102)], .012,
             collection, root, steel)
        box(f'Castor{i}_Fork', (x, y, .06), (.054, .036, .036),
            collection, root, steel, .006)
        # Axle along local Y; a capped cylinder made without context-sensitive ops.
        vertices = [(x + .035 * math.cos(t * math.tau / 32), y + dy,
                     .035 + .035 * math.sin(t * math.tau / 32))
                    for dy in (-.022, .022) for t in range(32)]
        faces = [(t, (t+1) % 32, (t+1) % 32 + 32, t+32) for t in range(32)]
        faces += [tuple(reversed(range(32))), tuple(range(32, 64))]
        mesh(f'Castor{i}_Tyre', vertices, faces, collection, root, rubber, .003)
        tube(f'Castor{i}_Axle', [(x, y-.025, .035), (x, y+.025, .035)],
             .009, collection, root, steel)
    tube('Pole', [(0, .20, .11), (0, .20, 1.72)], .014, collection, root, steel)
    box('PoleFoot', (0, .17, .13), (.085, .10, .025), collection, root, steel)


def sign(collection, root, white, navy, steel):
    box('SignFrame', (0, .20, 1.51), (.82, .034, .42), collection, root, steel, .015)
    box('SignBoard', (0, .20, 1.51), (.80, .04, .40), collection, root, white, .009)
    source = bpy.data.objects.get('SE_EntrySignText')
    for back in (False, True):
        name = 'SignText_Back' if back else 'SignText_Front'
        data = bpy.data.curves.new(PREFIX + name, 'FONT')
        data.body, data.align_x, data.align_y = 'BASKETS', 'CENTER', 'CENTER'
        data.size, data.extrude, data.bevel_depth = .135, .0003, .0001
        if source and source.type == 'FONT':
            data.font = source.data.font
        obj = attach(name, data, collection, root, navy)
        obj.location = (0, .222 if back else .178, 1.51)
        obj.rotation_euler = (math.pi / 2, 0, math.pi if back else 0)
        bpy.context.view_layer.update()
        if obj.dimensions.x > .70:
            obj.scale *= .70 / obj.dimensions.x


def bounds(obj, graph):
    evaluated = obj.evaluated_get(graph)
    points = [evaluated.matrix_world @ Vector(p) for p in evaluated.bound_box]
    return (Vector(tuple(min(p[i] for p in points) for i in range(3))),
            Vector(tuple(max(p[i] for p in points) for i in range(3))))


def overlaps(a, b):
    return all(a[0][i] < b[1][i] - .0001 and b[0][i] < a[1][i] - .0001
               for i in range(3))


def excluded_surface(obj, bbox):
    name = obj.name.casefold()
    # Only named floor/ceiling slabs and mats are exempt, never furniture/glass.
    named = re.search(r'floor|ceiling|slab|\bmat\b|_mat(?:_|\d|$)|mat(?:\.\d+)?$|doormat|'
                      r'zemin|tavan|paspas', name)
    size = bbox[1] - bbox[0]
    return bool(named and size.z < .5 and size.z < max(size.x, size.y))


def place(scene, root):
    layer = bpy.context.view_layer
    render_objects = set()

    def collect(collection):
        if collection.hide_render:
            return
        render_objects.update(o for o in collection.objects if not o.hide_render)
        for child in collection.children:
            collect(child)

    collect(scene.collection)
    layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    obstacles = []
    for obj in scene.objects:
        if obj.type != 'MESH' or obj.name.startswith(PREFIX):
            continue
        if obj not in render_objects and not obj.visible_get(view_layer=layer):
            continue
        bbox = bounds(obj, graph)
        if not excluded_surface(obj, bbox):
            obstacles.append((obj.name, bbox))
    parts = [o for o in scene.objects if o.parent == root and o.type != 'EMPTY']
    # Stay on the left of the gates; try nearest left positions first, then right.
    candidates = [8.5] + [8.5 - .1*i for i in range(1, 31)] + [8.5 + .1*i for i in range(1, 6)]
    for x in candidates:
        root.location = (x, -10.9, 0)
        # Local front is -Y; point it toward the arriving customer at the doors.
        root.rotation_euler.z = math.atan2(11.6-x, 1.1)
        layer.update()
        graph = bpy.context.evaluated_depsgraph_get()
        boxes = [bounds(obj, graph) for obj in parts]
        whole = (Vector(tuple(min(b[0][i] for b in boxes) for i in range(3))),
                 Vector(tuple(max(b[1][i] for b in boxes) for i in range(3))))
        # A conservative whole-stand AABB reserves space between the parts too.
        hits = [name for name, bbox in obstacles if overlaps(whole, bbox)]
        if hits:
            log(f'World-bounds overlap at x={x:.2f}: ' + ', '.join(hits))
            continue
        log(f'Final location: ({x:.2f}, -10.90, 0.00), yaw '
            f'{math.degrees(root.rotation_euler.z):.1f} degrees; no mesh overlaps. '
            f'World bounds: {tuple(whole[0])} .. {tuple(whole[1])}')
        return
    raise RuntimeError('No clear position left of the entrance gates; file not saved.')


def main():
    if not bpy.data.filepath:
        raise RuntimeError('Open the intended .blend first; no output path is guessed.')
    scene = bpy.data.scenes.get(SCENE)
    collection = bpy.data.collections.get(COLLECTION)
    if scene is None or collection is None or collection not in set(scene.collection.children_recursive):
        raise RuntimeError('Missing target scene or market collection in that scene.')
    bpy.context.window.scene = scene
    cleanup()
    root = attach('Root', None, collection, None)
    red = material('RedPlastic', (.65, .018, .025))
    steel = material('BrushedSteel', (.48, .52, .56), .32, 1)
    rubber = material('Rubber', (.018, .022, .028), .7)
    dark = material('DollyGrey', (.055, .065, .075), .42)
    white = material('SignWhite', (.92, .94, .96), .48)
    navy = material('SignNavy', (.008, .025, .085), .5)
    dolly(collection, root, dark, steel, rubber)
    for index in range(7):
        basket(index, collection, root, red, steel, rubber)
    sign(collection, root, white, navy, steel)
    place(scene, root)
    count = sum(o.name.startswith(PREFIX) for o in scene.objects)
    bpy.ops.wm.save_mainfile(compress=True)
    log(f'Saved {SCENE}: 7 nested baskets, 14 folded handles, 4 castors, '
        f'two-sided BASKETS sign; {count} generated objects.')


if __name__ == '__main__':
    main()

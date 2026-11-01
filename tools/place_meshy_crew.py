"""Kept in tools/ for the record; it runs against counterfoil/artifacts/ (not in the repo: the Meshy originals are 84–250 MB each).
Add the Meshy Reader, Runner and store manager to the approved Nella + PayPal scene.

Opens homi-nella-paypal.blend (never overwritten), imports the three Meshy originals, scales them to
character height, places them around the returns kiosk and the tills, shrinks their textures so the
saved file stays sane, and writes homi-crew.blend. Rendering and the web export are separate steps.
"""
import bpy, math, sys
from mathutils import Vector, Matrix

root = '/Users/kosesena/Desktop/paypal-ai-hackathon/counterfoil/artifacts/'
out = root + 'homi-meshy-preview/'
bpy.ops.wm.open_mainfile(filepath=out + 'homi-nella-paypal.blend')
s = bpy.context.scene


def place(obs, name, height, pos, angle):
    pts = [o.matrix_world @ Vector(v) for o in obs if o.type == 'MESH' for v in o.bound_box]
    lo = Vector(tuple(min(p[i] for p in pts) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    scale = height / (hi.z - lo.z)
    center = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    T = Matrix.Translation(Vector(pos)) @ Matrix.Rotation(math.radians(angle), 4, 'Z') @ Matrix.Scale(scale, 4) @ Matrix.Translation(-center)
    col = bpy.data.collections.new(name)
    s.collection.children.link(col)
    for o in obs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
        o.matrix_world = T @ o.matrix_world
        o.name = name + ' | ' + o.name
    print('PLACED', name, 'scale', round(scale, 3), 'at', pos, flush=True)


# (file, collection, height in scene units, floor position, facing angle; Nella is 2.05, PayPal 1.65)
crew = [
    # positions chosen in the browser so nobody hides behind Nella or in front of Counterfoil (2 Nov):
    # left to right in the camera: manager, Nella, Counterfoil (back), PayPal, Runner, Reader in the till aisle
    ('meshy-reader/reader-original.glb', 'Reader | Meshy', 1.72, (-8.0, -9.3, .015), 18),
    ('meshy-runner/runner-original.glb', 'Runner | Meshy', 1.95, (-8.95, -10.3, .015), 18),
    ('meshy-manager/manager-original.glb', 'Manager | Meshy', 1.88, (-14.55, -10.95, .015), 28),
]
for path, name, height, pos, angle in crew:
    before_obs, before_imgs = set(s.objects), set(bpy.data.images)
    bpy.ops.import_scene.gltf(filepath=root + path)
    obs = list(set(s.objects) - before_obs)
    place(obs, name, height, pos, angle)
    for im in set(bpy.data.images) - before_imgs:
        im.name = name + ' | ' + im.name
        # base colour stays 2048 like the exported Nella; the normal / ORM maps can be 1024
        limit = 2048 if im.name.endswith('Image_0') else 1024
        if max(im.size) > limit:
            r = limit / max(im.size)
            im.scale(round(im.size[0] * r), round(im.size[1] * r))
            im.pack()
    for m in {sl.material for o in obs if o.type == 'MESH' for sl in o.material_slots if sl.material}:
        m.name = name + ' | ' + m.name

s.render.filepath = out + 'homi-crew.png'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=out + 'homi-crew.blend')
print('SAVED', out + 'homi-crew.blend', flush=True)

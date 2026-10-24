"""Export the till area of the HOMI store as the dashboard's 3D scene.

    /Applications/Blender.app/Contents/MacOS/Blender -b docs/gorseller/counterfoil-magaza.blend \
        --python tools/export_station_glb.py -- dashboard/public/3d/homi-return-station.glb

Reads the .blend without saving it. Every visible mesh, curve and text whose centre lies in the level-1 till
area is baked at frame 640 (customer at the station) into a plain mesh, collection instances included;
walls and floor slabs (> 6 m) are left out because the page draws its own floor. Draco-compressed GLB.
"""
import bpy, sys
from mathutils import Vector
OUT = sys.argv[-1]
src = bpy.data.scenes["Counterfoil_Market_Composite"]; bpy.context.window.scene = src
src.frame_set(640); src.view_layers[0].update()
dg = bpy.context.evaluated_depsgraph_get()
X0, X1, Y0, Y1 = -19.6, -8.4, -12.3, -5.6           # till area on level 1
stage = bpy.data.scenes.new("__glb__"); made = 0; skipped = []; seen = set()
for inst in dg.object_instances:
    ob = inst.object
    if ob.type not in ("MESH", "CURVE", "FONT"): continue
    orig = ob.original
    if not orig.visible_get(view_layer=src.view_layers[0]) and not inst.is_instance: continue
    if orig.hide_render: continue
    M = inst.matrix_world.copy()
    cs = [M @ Vector(c) for c in ob.bound_box]
    lo = Vector([min(c[i] for c in cs) for i in range(3)]); hi = Vector([max(c[i] for c in cs) for i in range(3)])
    c = (lo + hi) / 2
    if not (X0 < c.x < X1 and Y0 < c.y < Y1 and -0.3 < c.z < 3.4): continue
    if max(hi - lo) > 6.0: skipped.append(orig.name); continue        # walls, floor slabs, facade
    key = (orig.name, tuple(round(v, 3) for v in M.translation))
    if key in seen: continue                                            # same object reached twice
    seen.add(key)
    try:
        me = bpy.data.meshes.new_from_object(ob, preserve_all_data_layers=False, depsgraph=dg)
    except Exception as e:
        continue
    if not me.polygons: continue
    o = bpy.data.objects.new(orig.name, me); o.matrix_world = M; stage.collection.objects.link(o); made += 1
print("GLB objects", made, "skipped big", sorted(set(skipped))[:20])
bpy.context.window.scene = stage
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_active_scene=True, export_apply=True,
                          export_animations=False, export_lights=False, export_cameras=False, export_yup=True, export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=7)
print("GLB written", OUT)

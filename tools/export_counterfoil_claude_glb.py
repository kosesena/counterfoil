"""Export the 3D Counterfoil (docs/gorseller/karakterler/counterfoil-claude-3d.blend, tools/counterfoil_claude_3d.py) for
the Overview hero: curves become meshes, the stage stays behind, Draco keeps it small.
Run: blender -b docs/gorseller/karakterler/counterfoil-claude-3d.blend --python tools/export_counterfoil_claude_glb.py
  -> dashboard/public/3d/counterfoil-claude.glb
"""
import bpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dashboard/public/3d/counterfoil-claude.glb'

root = bpy.data.objects['Counterfoil']
keep = [root] + list(root.children_recursive)
for o in list(bpy.data.objects):
    if o not in keep:
        bpy.data.objects.remove(o, do_unlink=True)

bpy.ops.object.select_all(action='DESELECT')
for o in keep:
    if o.type == 'CURVE':
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
bpy.ops.object.convert(target='MESH')
for o in bpy.data.objects:
    for m in list(o.modifiers):
        if m.type == 'PARTICLE_SYSTEM':
            o.modifiers.remove(m)

# the page draws its own felt (dashboard/app/counterfoil-3d.tsx): ship flat colours, no fibre tile
for m in bpy.data.materials:
    if not m.use_nodes or m.name.startswith('Bead'):
        continue
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out, b = nt.nodes.new('ShaderNodeOutputMaterial'), nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = m.diffuse_color
    b.inputs['Roughness'].default_value = 1.0
    nt.links.new(b.outputs['BSDF'], out.inputs['Surface'])

bpy.ops.object.select_all(action='SELECT')
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format='GLB', use_selection=True, export_apply=True,
                          export_yup=True, export_texcoords=False, export_normals=True,
                          export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
                          export_draco_position_quantization=12, export_draco_normal_quantization=8)
print('[CF] exported', OUT, OUT.stat().st_size)

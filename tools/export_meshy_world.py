"""Export a disposable browser copy of the approved Meshy store.
Usage: blender -b --python tools/export_meshy_world.py -- source.blend output-directory
Source is never saved. Procedural wool strands are omitted for browser performance.
Meshy UV textures and corrected PayPal label objects are retained.
"""
import bpy, json, numpy as np, sys
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
source,out=Path(args[0]),Path(args[1])
out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(source))
s=bpy.context.scene
cam=s.camera
(out/'camera.json').write_text(json.dumps({'position':list(cam.location),'quaternion':list(cam.rotation_euler.to_quaternion()),'scale':cam.data.ortho_scale,'target':[-11,-10.3,1.1]}))
# Export a disposable reduced copy only; never save the source .blend.
for o in list(s.objects):
 mats=getattr(o.data,'materials',[])
 fiber=any(m and any(word in m.name.lower() for word in ['yarn','strands']) for m in mats)
 if o.hide_render or fiber or o.type not in {'MESH','CURVE','FONT','SURFACE'}: bpy.data.objects.remove(o,do_unlink=True)
for o in s.objects:
 o.hide_set(False);o.hide_viewport=False
 for mod in list(o.modifiers):
  if mod.type in {'SUBSURF','BEVEL'}: o.modifiers.remove(mod)
 if o.type in {'CURVE','FONT'}:
  o.data.resolution_u=2;o.data.bevel_resolution=0
 if o.type=='MESH' and len(o.data.polygons)>200000:
  mesh=o.data; n=len(mesh.polygons)
  if len(mesh.loops)!=n*3: raise RuntimeError('Expected triangle mesh')
  co=np.empty(len(mesh.vertices)*3,dtype=np.float32);mesh.vertices.foreach_get('co',co);co=co.reshape(-1,3)
  cell=float(np.max(np.ptp(co,axis=0)))/160
  q=np.floor((co-co.min(axis=0))/cell).astype(np.int64)
  keys=q[:,0]+q[:,1]*512+q[:,2]*512*512
  _,inverse=np.unique(keys,return_inverse=True)
  count=np.bincount(inverse);coords=np.stack([np.bincount(inverse,weights=co[:,j])/count for j in range(3)],axis=1)
  loops=np.empty(n*3,dtype=np.int32);mesh.loops.foreach_get('vertex_index',loops)
  faces=inverse[loops].reshape(-1,3)
  valid=(faces[:,0]!=faces[:,1])&(faces[:,0]!=faces[:,2])&(faces[:,1]!=faces[:,2])
  chosen=np.flatnonzero(valid);faces=faces[valid]
  _,unique=np.unique(np.sort(faces,axis=1),axis=0,return_index=True)
  chosen=chosen[unique];faces=faces[unique]
  new=bpy.data.meshes.new(o.name+' web');new.from_pydata(coords.tolist(),[],faces.tolist());new.update()
  for mat in mesh.materials:new.materials.append(mat)
  if mesh.uv_layers.active:
   uv=np.empty(len(mesh.loops)*2,dtype=np.float32);mesh.uv_layers.active.data.foreach_get('uv',uv)
   new.uv_layers.new(name='UVMap').data.foreach_set('uv',uv.reshape(n,3,2)[chosen].ravel())
  for face in new.polygons:face.use_smooth=True
  o.data=new
  print('REDUCED',o.name,len(new.polygons),flush=True)
# Reduce image memory for browser while retaining the separate corrected label assets.
for im in bpy.data.images:
 if im.type=='IMAGE' and max(im.size)>2048:
  ratio=2048/max(im.size);im.scale(round(im.size[0]*ratio),round(im.size[1]*ratio))
# glTF cannot represent procedural noise: preserve its base colors with a simple PBR fallback.
for mat in bpy.data.materials:
 if not mat.use_nodes: continue
 bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if not bs: continue
 if 'PayPal' in mat.name or 'paypal' in mat.name:
  image=next((n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE'),None)
  if image:
   mat.node_tree.links.new(image.outputs['Color'],bs.inputs['Base Color'])
   mat.node_tree.links.new(image.outputs['Alpha'],bs.inputs['Alpha'])
 if 'felt' in mat.name.lower() or 'wool' in mat.name.lower():bs.inputs['Roughness'].default_value=.95
 for name in ['Base Color','Roughness','Normal']:
  inp=bs.inputs.get(name)
  if not inp:continue
  for link in list(inp.links):
   if link.from_node.type not in {'TEX_IMAGE','NORMAL_MAP','RGB'}:mat.node_tree.links.remove(link)
bpy.ops.object.select_all(action='SELECT')
bpy.context.view_layer.objects.active=next(iter(s.objects))
bpy.ops.object.convert(target='MESH')
# Batch static geometry, retaining separate materials and textures.
chars=[o for o in s.objects if o.name.startswith(('Nella |','PayPal |'))]
env=[o for o in s.objects if o not in chars and o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in env:o.select_set(True)
if env:
 bpy.context.view_layer.objects.active=env[0];bpy.ops.object.join();bpy.context.object.name='HOMI store and Counterfoil'
bpy.ops.object.select_all(action='SELECT')
print('EXPORT',len(s.objects),flush=True)
bpy.ops.export_scene.gltf(filepath=str(out/'homi-meshy.glb'),export_format='GLB',use_selection=True,export_animations=False,export_cameras=False,export_lights=False,export_apply=True,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
print('DONE', (out/'homi-meshy.glb').stat().st_size,flush=True)

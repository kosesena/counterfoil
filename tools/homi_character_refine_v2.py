"""Second proportion pass: upright oval heads, taller torsos and legs.
Run after homi_character_refine.py. Preserves prop positions and animation timing.
"""
import bpy
from mathutils import Matrix,Vector
s=bpy.data.scenes['Counterfoil_Market_Composite']
if s.get('homi_character_refine_v2'):raise RuntimeError('Already applied')
def affine(center,scale,shift=(0,0,0)):
 return Matrix.Translation(Vector(center)+Vector(shift))@Matrix.Diagonal((*scale,1))@Matrix.Translation(-Vector(center))
def edit(o,t):
 o.data=o.data.copy();o.data.transform(o.matrix_basis.inverted()@t@o.matrix_basis)
for role,cx in [('Customer',-3.6),('Store_Manager',-1.2)]:
 for o in bpy.data.collections['Cast_'+role].objects:
  if o.type not in {'MESH','CURVE'}:continue
  if o.parent_bone=='head':edit(o,affine((cx,0,2.26),(.78,.85,1.05),(0,0,.26)))
  elif o.name.endswith(('Torso','Apron','ApronPocket')):edit(o,affine((cx,0,1.375),(1,.95,1.25),(0,0,.14)))
  elif '_Leg' in o.name:edit(o,affine((o.location.x,0,.32),(1,1,1.17)))
  elif o.name.endswith('Neck'):edit(o,affine((cx,0,1.83),(.90,.90,1.12),(0,0,.18)))
base=open('/Users/kosesena/Desktop/paypal-ai-hackathon/tools/homi_p6_choreography.py').read()
exec(base[base.index('def inst_matrix'):base.index('# Handheld reader assembly')])
for role,sides,review in [('Customer',['R','L'],'HOMI_P6_Scan_Review'),('Store_Manager',['L'],'HOMI_P6_Manager_Review')]:
 sc=bpy.data.scenes[review];bpy.context.window.scene=sc
 for f in range(620,1141):
  sc.frame_set(f)
  for side in sides:
   parts={k:bpy.data.objects['PC_'+role+side+k] for k in ['upper','fore','elbow','palm','thumb']}
   contact=parts['palm'].location.copy()
   delta=inst_matrix(role).to_3x3()@Vector((-.055 if side=='R' else .055,0,.30))
   set_arm(parts,shoulder(role,side)+delta,contact,f,side)
s['homi_character_refine_v2']='Head narrower 22%, oval; torso taller 25%; legs taller17% relative to v1; prop contacts retained.'
# Full-length eye-level review without the counter hiding the silhouette.
r=bpy.data.scenes.new('HOMI_Character_Proportion_Review');r.world=bpy.data.scenes['HOMI_P6_Scan_Review'].world;r.render.engine=s.render.engine
r.collection.children.link(bpy.data.collections['HOMI_P6_Choreography'])
for name in ['Inst_Customer','HOMI_Review_Floor','PC_Key','PC_Fill']:r.collection.objects.link(bpy.data.objects[name])
for o in bpy.data.collections['HOMI_Return_Station'].objects:
 p=o
 while p.parent:p=p.parent
 if p.name.startswith('PC_Cup_') or p.name=='PC_Handheld':r.collection.objects.link(o)
d=bpy.data.cameras.new('PC_ProportionCamera');cam=bpy.data.objects.new('PC_ProportionCamera',d);r.collection.objects.link(cam);cam.location=(-16.8,-12.1,1.9);target=Vector((-12.65,-9.65,1.4));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=3.65;r.camera=cam
r.render.resolution_x=1400;r.render.resolution_y=1600;r.render.resolution_percentage=100
bpy.context.window.scene=r;r.frame_set(646);r.render.filepath='/Users/kosesena/Documents/Codex/2026-10-23/se/outputs/homi-character-proportions-v2.png';bpy.ops.render.render(write_still=True)
# Sena correction: retain a spherical toy-style head, not an elongated oval.
for role,cx in [('Customer',-3.6),('Store_Manager',-1.2)]:
 old=affine((cx,0,2.26),(.78,.85,1.05),(0,0,.26))
 spherical=affine((cx,0,2.26),(.9514,1.179,.8696),(0,0,.26))
 for o in bpy.data.collections['Cast_'+role].objects:
  if o.type in {'MESH','CURVE'} and o.parent_bone=='head':edit(o,spherical@old.inverted())
s['homi_character_refine_v2']='Round head approx radius .36; taller torso and legs; prop contacts retained. Sena explicitly requested spherical head.'
r.frame_set(646);bpy.ops.render.render(write_still=True)
# Short, visible neck suits the round-headed style.
for role in ['Customer','Store_Manager']:
 for o in bpy.data.collections['Cast_'+role].objects:
  if o.type in {'MESH','CURVE'} and o.parent_bone=='head':edit(o,Matrix.Translation((0,0,-.10)))
r=bpy.data.scenes['HOMI_P6_Scan_Review'];bpy.context.window.scene=r;r.frame_set(646)
cam=bpy.data.objects['PC_ScanCamera'];cam.location=(-16,-12.8,2.6);cam.rotation_euler=(Vector((-12.9,-9.6,1.45))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=4.8;r.camera=cam
r.render.filepath='/Users/kosesena/Documents/Codex/2026-10-23/se/outputs/homi-round-head-v2.png';bpy.ops.render.render(write_still=True)

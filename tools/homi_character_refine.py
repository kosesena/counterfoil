"""Refine HOMI human proportions without moving animated prop contacts.
Run once after P6 choreography scripts. Mesh-space edits leave rig/action timings intact.
"""
import bpy
from mathutils import Matrix, Vector
scene=bpy.data.scenes['Counterfoil_Market_Composite']
if scene.get('homi_character_refine_v1'):raise RuntimeError('Already refined')
def affine(center,scale,shift=(0,0,0)):
 return Matrix.Translation(Vector(center)+Vector(shift))@Matrix.Diagonal((*scale,1))@Matrix.Translation(-Vector(center))
def edit(o,transform):
 o.data=o.data.copy();o.data.transform(o.matrix_basis.inverted()@transform@o.matrix_basis)
for role,cx in [('Customer',-3.6),('Store_Manager',-1.2)]:
 for o in bpy.data.collections['Cast_'+role].objects:
  if o.type not in {'MESH','CURVE'}:continue
  if o.parent_bone=='head':edit(o,affine((cx,0,2.08),(.86,.86,.90),(0,0,.18)))
  elif o.name.endswith(('Torso','Apron','ApronPocket')):edit(o,affine((cx,0,1.27),(.88,.93,1.06),(0,0,.105)))
  elif '_Leg' in o.name:edit(o,affine((o.location.x,0,.32),(.94,.94,1.24)))
  elif o.name.endswith('Neck'):edit(o,affine((cx,0,1.71),(.86,.86,1.35),(0,0,.12)))
  elif '_Arm' in o.name:edit(o,affine(o.location,(.86,.90,1)))
  elif '_Hand' in o.name and 'Tablet' not in o.name:edit(o,affine(o.location,(.91,.91,.91)))
for o in bpy.data.collections['HOMI_P6_Choreography'].objects:
 if o.type=='MESH' and o.name.startswith(('PC_Customer','PC_Store_Manager')):
  o.data=o.data.copy()
  scale=(.88,.88,1) if o.name.endswith(('upper','fore')) else (.92,.92,.92)
  o.data.transform(Matrix.Diagonal((*scale,1)))
for name,color in [('CF_Skin',(.88,.65,.48,1)),('CF_SkinLight',(.94,.74,.58,1))]:
 m=bpy.data.materials[name];m.diffuse_color=color
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=color
 p.inputs['Roughness'].default_value=.48
scene['homi_character_refine_v1']='Head width -14%, head height -10%; legs +24%; torso width -12%; neck visible; light warm skin. Prop trajectories untouched.'
r=bpy.data.scenes['HOMI_P6_Scan_Review'];bpy.context.window.scene=r;r.frame_set(646)
r.camera=bpy.data.objects['PC_ScanCamera'];r.render.resolution_percentage=100
r.render.filepath='/Users/kosesena/Documents/Codex/2026-10-23/se/outputs/homi-character-refined.png'
bpy.ops.render.render(write_still=True)
# Refit sleeve chains to new shoulders while preserving every animated palm contact.
base=open('/Users/kosesena/Desktop/paypal-ai-hackathon/tools/homi_p6_choreography.py').read()
exec(base[base.index('def inst_matrix'):base.index('# Handheld reader assembly')])
for role,sides,review in [('Customer',['R','L'],'HOMI_P6_Scan_Review'),('Store_Manager',['L'],'HOMI_P6_Manager_Review')]:
 sc=bpy.data.scenes[review];bpy.context.window.scene=sc
 for f in range(620,1141):
  sc.frame_set(f)
  for side in sides:
   parts={k:bpy.data.objects['PC_'+role+side+k] for k in ['upper','fore','elbow','palm','thumb']}
   contact=parts['palm'].location.copy()
   delta=inst_matrix(role).to_3x3()@Vector((-.055 if side=='R' else .055,0,.105))
   set_arm(parts,shoulder(role,side)+delta,contact,f,side)
bpy.context.window.scene=r;r.frame_set(646)
cam=bpy.data.objects['PC_ScanCamera'];cam.location=(-15.0,-12.8,3.1);cam.rotation_euler=(Vector((-12.9,-9.6,1.35))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=4.1
r.camera=cam;r.render.filepath='/Users/kosesena/Documents/Codex/2026-10-23/se/outputs/homi-character-refined.png';bpy.ops.render.render(write_still=True)

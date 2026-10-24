"""Visual-QA refinements after homi_p6_choreography.py. Run in Blender; no save/commit.
Wrap labels, refine cup-handle contact and hand transitions, add manager fingertip,
and prepare isolated cameras. Existing receipt animation is deliberately untouched.
"""
import bpy, math
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
base=Path('/Users/kosesena/Desktop/paypal-ai-hackathon/tools/homi_p6_choreography.py').read_text()
c=bpy.data.collections['HOMI_P6_Choreography']
exec(base[base.index('WHITE='):base.index('# Internal-demo EAN')])
exec(base[base.index('def inst_matrix'):base.index('# Handheld reader assembly')])
def ease(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
r=bpy.data.scenes['HOMI_P6_Scan_Review'];bpy.context.window.scene=r
arms={side:{k:bpy.data.objects['PC_Customer'+side+k] for k in ['upper','fore','elbow','palm','thumb']} for side in ['R','L']}
roots=[bpy.data.objects['PC_Cup_%02d'%i] for i in range(1,5)]
scan=bpy.data.objects['PC_Handheld']
r.frame_set(619)
initial={side:inst_matrix('Customer')@bpy.data.objects['Customer_Hand'+('1' if side=='R' else '-1')].matrix_world.translation for side in ['R','L']}
for f in range(620,789):
 r.frame_set(f)
 rest={side:shoulder('Customer',side)+Vector((0,0,-.62)) for side in ['R','L']}
 idx=min(3,max(0,(f-632)//36));root=roots[idx]
 contact=root.location+root.rotation_quaternion@Vector((0,.16,.095))
 if f<632:right=initial['R'].lerp(contact,ease((f-620)/12))
 elif f>=772:right=(roots[3].location+Vector((0,.16,.095))).lerp(rest['R'],ease((f-772)/16))
 elif (f-632)%36>=32 and idx<3:
  upcoming=roots[idx+1].location+Vector((0,.16,.095));right=contact.lerp(upcoming,ease(((f-632)%36-32)/4))
 else:right=contact
 grip=scan.location+Vector((.025,0,-.015))
 if f<628:left=initial['L'].lerp(grip,ease((f-620)/8))
 elif f<=776:left=grip
 else:left=grip.lerp(rest['L'],ease((f-776)/12))
 for side,target in [('R',right),('L',left)]:set_arm(arms[side],shoulder('Customer',side),target,f,side)
for parts in arms.values():
 for o in parts.values():
  for fc in curves(o):
   if not fc.data_path.startswith('hide_'):
    for kp in reversed(list(fc.keyframe_points)):
     if kp.co.x>788:fc.keyframe_points.remove(kp,fast=True)
  for path in ['location','rotation_quaternion','scale']:o.keyframe_insert(path,frame=1140)
# Curved label meshes preserve editable source text/stripes hidden underneath.
r.frame_set(646);dg=bpy.context.evaluated_depsgraph_get()
for o in list(bpy.data.objects):
 if o.name.startswith(('PC_Label_','PC_LabelText_','PC_EAN_')) and not o.name.endswith('_Wrapped'):
  name=o.name+'_Wrapped'
  if not bpy.data.objects.get(name):
   mesh=bpy.data.meshes.new_from_object(o.evaluated_get(dg));mesh.transform(o.matrix_basis)
   for v in mesh.vertices:
    x,y,z=v.co;rad=.063+max(0,z-.028)*(.012/.137)+(.0009 if o.name.startswith('PC_Label_') else .0018)
    a=x/rad;v.co=(rad*math.sin(a),-rad*math.cos(a),z)
   n=bpy.data.objects.new(name,mesh);o.users_collection[0].objects.link(n);n.parent=o.parent;n['wrapped']=True
  o.hide_render=True;o.hide_viewport=True
# Explicit intermediate new-request state, before the second tap.
for prefix in ['P6_Tablet_','P6Review_P6_Tablet_']:
 rejected=bpy.data.objects[prefix+'State_780'];visibility(rejected,820,847)
 ready=bpy.data.objects.get(prefix+'Ready40')
 if not ready:
  ready=rejected.copy();ready.data=rejected.data.copy();ready.animation_data_clear();rejected.users_collection[0].objects.link(ready);ready.name=prefix+'Ready40'
 ready.data.body='NEW $40 / ready for approval';visibility(ready,848,859)
 bpy.data.objects[prefix+'State_860'].data.body='APPROVED $40 / GATEWAY RECHECK'
# Manager's two deliberate taps; no idle loop.
m=bpy.data.scenes.get('HOMI_P6_Manager_Review')
if not m:
 m=bpy.data.scenes.new('HOMI_P6_Manager_Review');m.collection.children.link(c)
 for name in ['Inst_Store_Manager','HOMI_Review_Floor']:m.collection.objects.link(bpy.data.objects[name])
 m.world=r.world;m.render.engine=r.render.engine
bpy.context.window.scene=m
parts={k:bpy.data.objects['PC_Store_ManagerL'+k] for k in ['upper','fore','elbow','palm','thumb']}
parts['palm'].scale=(.06,)*3
finger=bpy.data.objects.get('PC_ManagerIndex') or sphere('ManagerIndex',parts['palm'].data.materials[0],.012)
hand=bpy.data.objects['Store_Manager_Hand1'];m.frame_set(619);scale=hand.scale.copy()
hand.keyframe_insert('scale',frame=619);hand.scale=scale*.65;hand.keyframe_insert('scale',frame=620);hand.keyframe_insert('scale',frame=1140)
screen=bpy.data.objects['Store_Manager_HandTabletScreen']
for f in range(780,901):
 m.frame_set(f);world=inst_matrix('Store_Manager')@screen.matrix_world;normal=(world.to_3x3()@Vector((0,0,1))).normalized()
 w=ease(max(0,1-abs(f-819)/12,1-abs(f-859)/12))
 rest=shoulder('Store_Manager','L')+Vector((0,0,-.62));palm=rest.lerp(world@Vector((.08,-.075,.095)),w)
 set_arm(parts,shoulder('Store_Manager','L'),palm,f,'L');end=palm-normal*.089
 finger.location=(palm+end)/2;finger.rotation_mode='QUATERNION';finger.rotation_quaternion=(end-palm).to_track_quat('Z','Y');finger.scale=(.012,.012,.0445)
 for path in ['location','rotation_quaternion','scale']:finger.keyframe_insert(path,frame=f)
 finger.hide_render=w<.02;finger.hide_viewport=w<.02
 for path in ['hide_render','hide_viewport']:finger.keyframe_insert(path,frame=f)
for f in [1,779,901,1140]:
 finger.hide_render=True;finger.hide_viewport=True
 for path in ['hide_render','hide_viewport']:finger.keyframe_insert(path,frame=f)
# Readable review cameras for video editing.
def camera(scene,name,location,target,scale):
 o=bpy.data.objects.get(name)
 if not o:
  o=bpy.data.objects.new(name,bpy.data.cameras.new(name));scene.collection.objects.link(o)
 o.location=location;o.rotation_mode='XYZ';o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o.data.type='ORTHO';o.data.ortho_scale=scale
 return o
camera(r,'PC_ScanCamera',(-14.8,-12.2,2.7),(-12.95,-9.6,1.35),3.4)
camera(r,'PC_LabelCamera',(-13.38,-9.05,1.7),(-13,-9.62,1.34),.72)
m.frame_set(822);world=inst_matrix('Store_Manager')@screen.matrix_world;normal=(world.to_3x3()@Vector((0,0,1))).normalized()
cam=camera(m,'PC_ManagerCamera',world.translation+normal*.65,world.translation,.42);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=world.to_quaternion();m.camera=cam
if not bpy.data.objects.get('PC_ManagerKey'):
 d=bpy.data.lights.new('PC_ManagerKey','AREA');d.energy=60;d.size=2;o=bpy.data.objects.new('PC_ManagerKey',d);m.collection.objects.link(o);o.location=world.translation+normal*2;o.rotation_euler=(-normal).to_track_quat('-Z','Y').to_euler()
for scene in [r,m]:
 scene.frame_start=620;scene.frame_end=1140;scene.render.fps=24;scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
for o in c.objects:linear(o)
bpy.context.window.scene=r;r.camera=bpy.data.objects['PC_ScanCamera'];r.frame_set(646)
print('P6 final contact, wrapped labels and manager choreography applied.')
# State-dependent arithmetic: rejected request must not look like the approved one.
for prefix in ['P6_Tablet_','P6Review_P6_Tablet_']:
 for tag,body in [('Sum','$60 + $40 = $100 / within RMA'),('Reason','NEW REQUEST / GATEWAY RECHECK')]:
  old=bpy.data.objects[prefix+tag];visibility(old,780,859)
  new=bpy.data.objects.get(prefix+tag+'_Corrected')
  if not new:
   new=old.copy();new.data=old.data.copy();new.animation_data_clear();old.users_collection[0].objects.link(new);new.name=prefix+tag+'_Corrected'
  new.data.body=body;visibility(new,860,1140)
# Subdivide backing before wrapping, so its face follows the cup instead of a chord.
import bmesh
bpy.context.window.scene=r;r.frame_set(646);dg=bpy.context.evaluated_depsgraph_get()
for i in range(1,5):
 original=bpy.data.objects['PC_Label_%02d'%i];wrapped=bpy.data.objects[original.name+'_Wrapped']
 mesh=bpy.data.meshes.new_from_object(original.evaluated_get(dg));mesh.transform(original.matrix_basis)
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=24,use_grid_fill=True);bm.to_mesh(mesh);bm.free()
 for v in mesh.vertices:
  x,y,z=v.co;rad=.063+max(0,z-.028)*(.012/.137)+.0009;a=x/rad;v.co=(rad*math.sin(a),-rad*math.cos(a),z)
 wrapped.data=mesh
camera(r,'PC_LabelCamera',(-13.12,-9.0,1.59),(-13,-9.62,1.34),.62)

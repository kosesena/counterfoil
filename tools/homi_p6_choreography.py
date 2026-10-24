"""P6 filmed choreography. Four labeled cups, arm contact, scan pulses and manager taps.
Run once in the current Blender file. No payment execution and no git operations.
"""
import bpy, math
from mathutils import Vector, Matrix, Quaternion
s=bpy.data.scenes['Counterfoil_Market_Composite'];bpy.context.window.scene=s
if bpy.data.collections.get('HOMI_P6_Choreography'):raise RuntimeError('Already applied')
c=bpy.data.collections.new('HOMI_P6_Choreography');s.collection.children.link(c)
station=bpy.data.collections['HOMI_Return_Station']
WHITE=bpy.data.materials['HR_White'];INK=bpy.data.materials['HR_Ink']
def adopt(o,name,mat,col=c):
 o.name='PC_'+name
 for old in list(o.users_collection):old.objects.unlink(o)
 col.objects.link(o)
 if mat:o.data.materials.append(mat)
 return o
def box(name,loc,dims,mat,col=c):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=adopt(bpy.context.object,name,mat,col);o.scale=dims
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 b=o.modifiers.new('Soft edges','BEVEL');b.width=.002;b.segments=3;return o
def sphere(name,mat,rad):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12);o=adopt(bpy.context.object,name,mat);o.scale=(rad,rad,rad)
 for p in o.data.polygons:p.use_smooth=True
 return o
def curves(o):
 a=o.animation_data.action if o.animation_data else None
 if a:
  for l in a.layers:
   for strip in l.strips:
    for bag in strip.channelbags:yield from bag.fcurves

def visibility(o,start,end=1140):
 # Replace visibility tracks only; preserve transform tracks.
 for fc in list(curves(o)):
  if fc.data_path in ['hide_render','hide_viewport']:
   for kp in reversed(list(fc.keyframe_points)):fc.keyframe_points.remove(kp,fast=True)
 for f,h in [(1,True),(start-1,True),(start,False),(end,False),(end+1,True)]:
  o.hide_render=h;o.hide_viewport=h;o.keyframe_insert('hide_render',frame=f);o.keyframe_insert('hide_viewport',frame=f)
def retire(o):
 for f,h in [(1,False),(619,False),(620,True)]:
  o.hide_render=h;o.hide_viewport=h;o.keyframe_insert('hide_render',frame=f);o.keyframe_insert('hide_viewport',frame=f)
def linear(o):
 for fc in curves(o):
  for k in fc.keyframe_points:k.interpolation='CONSTANT' if fc.data_path.startswith('hide_') else 'LINEAR'
def text(name,body,loc,size,mat=INK,col=c):
 d=bpy.data.curves.new(name,'FONT');d.body=body;d.size=size
 o=bpy.data.objects.new('PC_'+name,d);col.objects.link(o);o.location=loc;d.materials.append(mat);return o
# Internal-demo EAN-13, valid check digit; no external brand/GS1 claim.
base='200105700001';check=(-sum(int(v)*(1 if i%2==0 else 3) for i,v in enumerate(base)))%10;ean=base+str(check)
L=['0001101','0011001','0010011','0111101','0100011','0110001','0101111','0111011','0110111','0001011']
parity=['LLLLLL','LLGLGG','LLGGLG','LLGGGL','LGLLGG','LGGLLG','LGGGLL','LGLGLG','LGLGGL','LGGLGL'][int(ean[0])]
bits='101'
for v,p in zip(ean[1:7],parity):
 pat=L[int(v)]
 if p=='G':pat=''.join('1' if b=='0' else '0' for b in pat[::-1])
 bits+=pat
bits+='01010'
for v in ean[7:]:bits+=''.join('1' if b=='0' else '0' for b in L[int(v)])
bits+='101'
roots=[]
starts=[Vector((-13.50,-9.93,.998)),Vector((-13.50,-9.63,.998)),Vector((-13.30,-9.93,.998)),Vector((-13.30,-9.63,.998))]
for idx,start in enumerate(starts,1):
 root=bpy.data.objects.new('PC_Cup_%02d'%idx,None);station.objects.link(root);root.location=start;roots.append(root)
 cup=bpy.data.objects['P6_ReturnCup_%02d'%idx];cup.data.transform(Matrix.Translation(-start));cup.parent=root;cup.matrix_parent_inverse=Matrix.Identity(4);cup.location=(0,0,0)
 handle=bpy.data.objects['P6_CupHandle_%02d'%idx];world=handle.matrix_world.copy();handle.parent=root;handle.matrix_parent_inverse=Matrix.Identity(4);handle.matrix_basis=Matrix.Translation(-start)@world
 label=box('Label_%02d'%idx,(0,0,0),(.112,.001,.108),WHITE,station);label.parent=root;label.location=(0,-.074,.095)
 for j,(line,z,size) in enumerate([('HOMI · Cloudstone cup',.137,.0062),('CUP · 25.00 USD',.126,.0060),(ean,.050,.0070)]):
  t=text('LabelText_%02d_%d'%(idx,j),line,(-.052,-.075,.0),size,INK,station);t.parent=root;t.location.z=z;t.rotation_euler=(math.pi/2,0,0)
 for j,b in enumerate(bits):
  if b=='1':
   guard=j<3 or 45<=j<50 or j>=92
   bar=box('EAN_%02d_%02d'%(idx,j),(0,0,0),(.00088,.0007,.054 if guard else .047),INK,station);bar.parent=root;bar.location=(-.048+j*.00102,-.075,.089)
 root['demo_ean13']=ean
# Freeze the original idle/pay actions only from 620 onward.
for role in ['Customer','Store_Manager']:
 rig=bpy.data.objects['CF_Rig_'+role];s.frame_set(619)
 poses={p.name:(p.rotation_quaternion.copy(),p.location.copy(),p.scale.copy()) for p in rig.pose.bones}
 for fc in curves(rig):
  for mod in list(fc.modifiers):
   if mod.type=='CYCLES':fc.modifiers.remove(mod)
  for k in reversed(list(fc.keyframe_points)):
   if k.co.x>=620:fc.keyframe_points.remove(k,fast=True)
 for p in rig.pose.bones:
  q,loc,scale=poses[p.name];p.rotation_quaternion=q;p.location=loc;p.scale=scale
  for f in [620,1140]:
   p.keyframe_insert('rotation_quaternion',frame=f);p.keyframe_insert('location',frame=f);p.keyframe_insert('scale',frame=f)
# Procedural two-link arms replace original rigid limbs during the shot.
def new_arm(role,side):
 suffix='1' if side=='R' else '-1'
 arm=bpy.data.objects[role+'_Arm'+suffix];hand=bpy.data.objects[role+'_Hand'+suffix]
 retire(arm);retire(hand)
 cloth=arm.data.materials[0];skin=hand.data.materials[0]
 parts={}
 for key,mat,r in [('upper',cloth,.103),('fore',cloth,.085),('elbow',cloth,.095),('palm',skin,.083),('thumb',skin,.033)]:
  parts[key]=sphere(role+side+key,mat,r);visibility(parts[key],620)
 return parts
arms={side:new_arm('Customer',side) for side in ['R','L']};manager_arm=new_arm('Store_Manager','L')
for name in ['Customer_ShoppingBag','Customer_BagHandle']:
 if bpy.data.objects.get(name):retire(bpy.data.objects[name])
def inst_matrix(role):
 inst=bpy.data.objects['Inst_'+role];return inst.matrix_world@Matrix.Translation(-inst.instance_collection.instance_offset)
def shoulder(role,side):
 rig=bpy.data.objects['CF_Rig_'+role];return inst_matrix(role)@rig.matrix_world@rig.pose.bones['upper_arm.'+side].head

def set_arm(parts,a,b,f,side='R'):
 a,b=Vector(a),Vector(b);d=b-a;dist=d.length
 # Elbow remains below the hand and outside the torso; two tapered sleeve segments.
 elbow=(a+b)*.5+Vector((.08,-.13 if side=='R' else .13,-.16))
 for key,p1,p2,r in [('upper',a,elbow,.103),('fore',elbow,b,.085)]:
  o=parts[key];v=p2-p1;o.location=(p1+p2)*.5;o.rotation_mode='QUATERNION';o.rotation_quaternion=v.to_track_quat('Z','Y');o.scale=(r,r,v.length*.5+.03)
  o.keyframe_insert('location',frame=f);o.keyframe_insert('rotation_quaternion',frame=f);o.keyframe_insert('scale',frame=f)
 for key,loc in [('elbow',elbow),('palm',b),('thumb',b+Vector((-.045,.035,-.025)))]:
  o=parts[key];o.location=loc;o.keyframe_insert('location',frame=f)
# Handheld reader assembly rotates from its cradle to point at the label.
scan=bpy.data.objects.new('PC_Handheld',None);station.objects.link(scan);scan.location=(-13.315,-9.4618,1.16)
for o in list(station.objects):
 if o.name.startswith(('HS_02_Hand','HS_02_Trigger')):
  world=o.matrix_world.copy();o.parent=scan;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=Matrix.Translation(-scan.location)@world
scan['rest_location']=list(scan.location)
red=bpy.data.materials.new('PC_ScanRed');red.use_nodes=True;n=red.node_tree.nodes;n.clear();e=n.new('ShaderNodeEmission');e.inputs['Color'].default_value=(1,.005,.001,1);e.inputs['Strength'].default_value=4;o=n.new('ShaderNodeOutputMaterial');red.node_tree.links.new(e.outputs[0],o.inputs[0])
# A narrow beam connects optical window to the label only during each read.
beam=box('ScanBeam',(0,0,0),(.002,.002,.002),red);visibility(beam,640,642)
# Safe short step to the scanner, followed by a stationary stance.
customer=bpy.data.objects['Inst_Customer'];s.frame_set(619);initial=customer.location.copy()
for fc in curves(customer):
 if fc.data_path=='location':
  for k in reversed(list(fc.keyframe_points)):
   if k.co.x>=620:fc.keyframe_points.remove(k,fast=True)
customer.location=initial;customer.keyframe_insert('location',frame=620)
customer.location=(-12.63,-9.65,-.16);customer.keyframe_insert('location',frame=628);customer.keyframe_insert('location',frame=1140)
# 36-frame cycles; first movement starts after the short approach.
scan_frames=[646,682,718,754]
def ease(t):t=max(0,min(1,t));return t*t*(3-2*t)
def lerp(a,b,t):return Vector(a).lerp(Vector(b),ease(t))
scan_rest=Vector(scan['rest_location']);scan_hold=Vector((-13.00,-9.39,1.18))
# The scanner's optical window is +X and +Z relative to its grip; turn +X toward -Y.
scan_rot=Quaternion((0,0,1),-math.pi/2)
for f in range(620,1141):
 s.frame_set(f)
 if f<634:t=ease((f-628)/6);scan.location=scan_rest.lerp(scan_hold,t);scan.rotation_mode='QUATERNION';scan.rotation_quaternion=Quaternion().slerp(scan_rot,t)
 elif f<=764:scan.location=scan_hold;scan.rotation_quaternion=scan_rot
 elif f<776:t=ease((f-764)/12);scan.location=scan_hold.lerp(scan_rest,t);scan.rotation_quaternion=scan_rot.slerp(Quaternion(),t)
 else:scan.location=scan_rest;scan.rotation_quaternion=Quaternion()
 scan.keyframe_insert('location',frame=f);scan.keyframe_insert('rotation_quaternion',frame=f)
 active=None
 for i,root in enumerate(roots):
  begin=632+i*36;dt=f-begin;origin=starts[i];held=Vector((-13.00,-9.65,1.25))
  root.rotation_mode='QUATERNION'
  if dt<0 or dt>=32:root.location=origin;root.rotation_quaternion=Quaternion()
  elif dt<10:root.location=lerp(origin,held,dt/10);root.rotation_quaternion=Quaternion().slerp(Quaternion((0,0,1),math.pi),ease(dt/10));active=i
  elif dt<18:root.location=held;root.rotation_quaternion=Quaternion((0,0,1),math.pi);active=i
  else:root.location=lerp(held,origin,(dt-18)/14);root.rotation_quaternion=Quaternion((0,0,1),math.pi).slerp(Quaternion(),ease((dt-18)/14));active=i
  root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_quaternion',frame=f)
 # Palm contacts the mug handle through the same transform; no independent floating cup motion.
 if active is not None:
  root=roots[active];right=root.location+root.rotation_quaternion@Vector((0,.105,.095))
 else:
  upcoming=min(3,max(0,(f-632)//36));root=roots[upcoming]
  right=root.location+Vector((0,.105,.095)) if 628<=f<776 else shoulder('Customer','R')+Vector((0,0,-.62))
 if 628<=f<776:left=scan.location+Vector((.025,0,-.015))
 else:left=shoulder('Customer','L')+Vector((0,0,-.62))
 set_arm(arms['R'],shoulder('Customer','R'),right,f,'R');set_arm(arms['L'],shoulder('Customer','L'),left,f,'L')
 # Pulse from the reader's optical window to the currently held cup label.
 on=any(k<=f<=k+2 for k in scan_frames)
 beam.hide_render=not on;beam.hide_viewport=not on;beam.keyframe_insert('hide_render',frame=f);beam.keyframe_insert('hide_viewport',frame=f)
 if on:
  i=scan_frames.index(next(k for k in scan_frames if k<=f<=k+2));root=roots[i]
  start=scan.location+scan.rotation_quaternion@Vector((.077,0,.155));end=root.location+root.rotation_quaternion@Vector((0,-.077,.09));v=end-start
  beam.location=(start+end)*.5;beam.rotation_mode='QUATERNION';beam.rotation_quaternion=v.to_track_quat('Z','Y');beam.scale=(1.2,1.2,v.length/.002)
  beam.keyframe_insert('location',frame=f);beam.keyframe_insert('rotation_quaternion',frame=f);beam.keyframe_insert('scale',frame=f)
# Customer UI sequence, preserving correction/provider/receipt timing.
for f,a,b in [(620,768,779),(680,780,819),(780,820,859),(860,860,949),(950,950,1019),(1020,1020,1140)]:
 for tag in ['UIRecord','UIAmount','UIOrderTotal','UIReview','UIHelp']:visibility(bpy.data.objects['HF_'+tag+'_'+str(f)],a,b)
bpy.data.objects['HF_UIRecord_620'].data.body='APPROVED RETURN'
bpy.data.objects['HF_UIHelp_620'].data.body='Approved return 100.00 USD'
for num,a,b in [(0,620,645),(1,646,681),(2,682,717),(3,718,753),(4,754,767)]:
 values={'UIRecord':'CLOUDSTONE CUP / CUP','UIAmount':str(num)+'/4','UIOrderTotal':'25.00 USD each / RMA-1057','UIReview':'SCAN EACH CUP','UIHelp':'Hold the product label to the reader.'}
 for tag,value in values.items():
  original=bpy.data.objects['HF_'+tag+'_620'];o=original.copy();o.data=original.data.copy();o.animation_data_clear();station.objects.link(o);o.name='PC_ScanUI_'+str(num)+'_'+tag;o.data.body=value;visibility(o,a,b)
# Manager notices amber, looks down and performs deliberate screen taps.
rig=bpy.data.objects['CF_Rig_Store_Manager']
def pose_angle(pb,x):
 basis=pb.bone.matrix_local.to_quaternion().inverted();return Quaternion(basis@Vector((1,0,0)),math.radians(x))
for f,x in [(620,0),(779,0),(792,24),(820,24),(860,24),(890,18),(1140,18)]:
 p=rig.pose.bones['head'];p.rotation_quaternion=pose_angle(p,x);p.keyframe_insert('rotation_quaternion',frame=f)
for f,x in [(620,-55),(779,-55),(795,-68),(880,-68),(900,-55),(1140,-55)]:
 p=rig.pose.bones['upper_arm.R'];p.rotation_quaternion=pose_angle(p,x);p.keyframe_insert('rotation_quaternion',frame=f)
# Target the actual animated tablet plane, in the manager's collection instance.
for f in range(620,1141):
 s.frame_set(f);bpy.context.view_layer.update()
 screen=bpy.data.objects['Store_Manager_HandTabletScreen'];world=inst_matrix('Store_Manager')@screen.matrix_world
 tap=world@Vector((.035,-.012,.045));rest=shoulder('Store_Manager','L')+Vector((0,0,-.62))
 weight=max(max(0,1-abs(f-819)/12),max(0,1-abs(f-859)/12))
 target=rest.lerp(tap,ease(weight));set_arm(manager_arm,shoulder('Store_Manager','L'),target,f,'L')
# Tablet visible state and explicit decisions.
for prefix in ['P6_Tablet_','P6Review_P6_Tablet_']:
 for old,a,b,value in [('State_620',780,819,'Requested $60 / BLOCK ($20 over)'),('State_780',820,859,'REJECTED / $60 request'),('State_860',860,949,'APPROVE $40 / GATEWAY RECHECK'),('State_950',950,1019,'$40 sent / awaiting confirmation'),('State_1020',1020,1140,'Provider confirmed $40 / receipt')]:
  o=bpy.data.objects.get(prefix+old)
  if o:o.data.body=value;visibility(o,a,b)
# Correct event markers. Amber and provider timing are left intact.
for marker in list(s.timeline_markers):
 if marker.frame>=620:s.timeline_markers.remove(marker)
for frame,name in [(620,'SCAN START'),(646,'CUP 1/4'),(682,'CUP 2/4'),(718,'CUP 3/4'),(754,'CUP 4/4'),(768,'APPROVED RETURN 100 USD'),(780,'REVIEW REQUIRED'),(820,'MANAGER REJECTED 60 USD'),(860,'APPROVE NEW 40 USD / RECHECK'),(950,'PROVIDER PENDING'),(1020,'PROVIDER CONFIRMED'),(1055,'RECEIPT OUT')]:s.timeline_markers.new(name,frame=frame)
for o in list(c.objects)+roots+[scan]:linear(o)
s['homi_p6_choreography']='Four EAN-labelled cups scan 646/682/718/754; approved 768; amber780; reject820; approve40/recheck860; provider1020; receipt1055. Scripted Blender demo, not live backend.'
s.frame_set(646)
# Isolated shot retains the actual animated customer, counter, props and arms.
r=bpy.data.scenes.new('HOMI_P6_Scan_Review');r.collection.children.link(station);r.collection.children.link(c);r.collection.children.link(bpy.data.collections['HOMI_Return_Finish']);r.collection.objects.link(customer)
r.collection.objects.link(bpy.data.objects['HOMI_Review_Floor']);r.world=bpy.data.scenes['HOMI_Checkout_Design_Review'].world;r.render.engine=s.render.engine
camdata=bpy.data.cameras.new('PC_ScanCamera');cam=bpy.data.objects.new('PC_ScanCamera',camdata);r.collection.objects.link(cam);s.collection.objects.link(cam);cam.location=(-10.7,-12.8,3.2);target=Vector((-12.9,-9.65,1.25));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camdata.type='ORTHO';camdata.ortho_scale=3.6;r.camera=cam
for name,loc,power in [('Key',(-10,-11,5),500),('Fill',(-14,-7,4),350)]:
 d=bpy.data.lights.new('PC_'+name,'AREA');d.energy=power;d.size=3;o=bpy.data.objects.new('PC_'+name,d);r.collection.objects.link(o);o.location=loc;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
r.frame_start=620;r.frame_end=1140;r.render.fps=24;r.render.resolution_x=1920;r.render.resolution_y=1080;r.render.resolution_percentage=75
bpy.context.window.scene=r;r.frame_set(646);r.render.filepath='/Users/kosesena/Documents/Codex/2026-10-23/se/outputs/homi-p6-scan-contact.png'
print('Created choreography; EAN',ean)

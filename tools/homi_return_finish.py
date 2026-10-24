"""HOMI close-up details and explicitly simulated refund screen timeline.
Run once on the existing store. Does not implement real refunds or hand IK.
"""
import bpy, math
from mathutils import Vector
s=bpy.data.scenes['Counterfoil_Market_Composite']
bpy.context.window.scene=s
if bpy.data.collections.get('HOMI_Return_Finish'): raise RuntimeError('Already applied')
c=bpy.data.collections.new('HOMI_Return_Finish');s.collection.children.link(c)
for sn in ['HOMI_Checkout_Design_Review','HOMI_Three_Checkouts_Review']:
 bpy.data.scenes[sn].collection.children.link(c)
def box(name,loc,dims,mat,r=.003):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name='HF_'+name
 for col in list(o.users_collection):col.objects.unlink(o)
 c.objects.link(o);o.scale=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 b=o.modifiers.new('Edge finish','BEVEL');b.width=r;b.segments=3
 o.data.materials.append(bpy.data.materials['HR_'+mat]);return o
def text(name,body,loc,size,mat='Ink'):
 d=bpy.data.curves.new(name,'FONT');d.body=body;d.size=size
 o=bpy.data.objects.new('HF_'+name,d);c.objects.link(o);o.location=loc;o.rotation_euler=(math.pi/2,0,math.pi/2);d.materials.append(bpy.data.materials['HR_'+mat]);return o
def visible(o,start,end):
 for f,h in [(1,True),(start-1,True),(start,False),(end,False),(end+1,True)]:
  o.hide_render=h;o.keyframe_insert('hide_render',frame=f)
# Modest roughness variation; no conspicuous grunge on a clean retail fixture.
for name,strength,scale in [('Porcelain',.07,160),('Forest',.04,210),('Ceramic',.035,130)]:
 m=bpy.data.materials['HR_'+name];n=m.node_tree.nodes;l=m.node_tree.links
 p=next(x for x in n if x.type=='BSDF_PRINCIPLED')
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=strength;bump.inputs['Distance'].default_value=.001
 l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
# Service-panel seams, feet and scanner-cable grommets.
for prefix in ['HR','HP01','HP03']:
 top=bpy.data.objects[prefix+'_Top'];x,y,z=top.location;w=top.dimensions.y
 for side in [-1,1]:
  box(prefix+'SideSeam'+str(side),(x+.366,y+side*(w/2-.12),.44),(.004,.008,.49),'Ink',.001)
  box(prefix+'Foot'+str(side),(x,y+side*(w/2-.18),.035),(.53,.12,.07),'Ink',.012)
 # Discreet circular power/data grommet behind the terminal.
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.027,depth=.006,location=(x-.27,y+.50,.975))
 o=bpy.context.object;o.name='HF_'+prefix+'_Grommet'
 for col in list(o.users_collection):col.objects.unlink(o)
 c.objects.link(o);o.data.materials.append(bpy.data.materials['HR_Ink'])
# Product SKU label on the visible front rim of the returned tray.
x,y,z=bpy.data.objects['HR_ReturnTrayBase'].location
box('ProductLabel',(x+.158,y,1.035),(.003,.18,.036),'White',.001)
text('SKU','HOMI  TRAY-030',(x+.160,y-.08,1.032),.009)
for i in range(24):
 box('Barcode%02d'%i,(x+.161,y-.077+i*.006,1.048),(.002,.0015 if i%3 else .003,.012),'Ink',.0002)
# Screen states: every state retains the authoritative amount and original total.
fields=['UIRecord','UIAmount','UIOrderTotal','UIReview','UIHelp']
for tag in fields:
 o=bpy.data.objects['HR_'+tag]
 for f,h in [(1,False),(619,False),(620,True)]:
  o.hide_render=h;o.keyframe_insert('hide_render',frame=f)
states=[
 (620,679,['RETURN RECORD / TRAY','$30.00','Original order  $90.00','SCAN MATCHED','Store record: RMA-030']),
 (680,779,['AGENT REQUEST','$90.00','Store-authorized refund  $30.00','BLOCKED / MISMATCH','No refund has been sent.']),
 (780,859,['MANAGER DECISION','$90.00','Store-authorized refund  $30.00','REQUEST REJECTED','Create a new request for $30.00.']),
 (860,949,['NEW REQUEST','$30.00','Original order  $90.00','GATEWAY RECHECK','Checking the new request again.']),
 (950,1019,['VERIFIED REQUEST','$30.00','Original order  $90.00','REFUND PROCESSING','Awaiting provider confirmation.']),
 (1020,1140,['PROVIDER CONFIRMED','$30.00','Original order  $90.00','REFUND COMPLETE','Collect your refund receipt.'])]
for a,b,values in states:
 for tag,value in zip(fields,values):
  original=bpy.data.objects['HR_'+tag];o=original.copy();o.data=original.data.copy();o.animation_data_clear();o.name='HF_'+tag+'_'+str(a);c.objects.link(o);o.data.body=value
  visible(o,a,b)
 marker=s.timeline_markers.new(values[3],frame=a)
text('Simulation','SANDBOX / DEMO',( -13.486,-8.976,1.325),.018,'Teal')
# A curved thermal receipt emerges only after simulated provider confirmation.
px,py,pz=bpy.data.objects['HR_PrinterSlot'].location
verts=[];faces=[]
for i in range(17):
 t=i/16;xx=px+.008+.08*math.sin(t*math.pi/2);zz=pz-.25*t
 verts.extend([(xx,py-.10,zz),(xx,py+.10,zz)])
 if i:faces.append((2*i-2,2*i-1,2*i+1,2*i))
mesh=bpy.data.meshes.new('Receipt');mesh.from_pydata(verts,[],faces);mesh.materials.append(bpy.data.materials['HR_White'])
o=bpy.data.objects.new('HF_Receipt',mesh);c.objects.link(o);visible(o,1020,1140)
# Collapse toward the printer slot, then feed the paper downwards.
for f,k in [(1020,.01),(1055,1)]:
 o.scale.z=k;o.location.z=pz*(1-k);o.keyframe_insert('scale',frame=f);o.keyframe_insert('location',frame=f)
for i,line in enumerate(['HOMI','REFUND RECEIPT','TRAY  $30.00','RMA-030','SANDBOX DEMO']):
 ob=text('ReceiptText'+str(i),line,(px+.095,py-.085,pz-.06-i*.03),.013 if i else .025)
 visible(ob,1055,1140)
s.frame_end=1140;s['homi_refund_timeline']='620 scan matched; 680 $90 held; 780 manager rejection; 860 fresh $30 recheck; 950 pending; 1020 simulated provider success; 1055 receipt. No live backend.'
s['homi_remaining_animation']='Customer hand grip/contact, receipt QR presentation, tray scan movement, manager tablet gesture and audio still need choreography.'
s.frame_set(740)
print('Close-up finish and six refund timeline states added; character choreography remains explicitly pending')
# Viewport visibility follows the same keys as renders.
for obj in bpy.data.objects:
 if not (obj.name.startswith('HF_') or obj.name in ['HR_'+tag for tag in fields]): continue
 ad=obj.animation_data
 if not ad or not ad.action: continue
 pairs=[]
 for layer in ad.action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     if fc.data_path=='hide_render':pairs.extend((int(k.co.x),bool(k.co.y)) for k in fc.keyframe_points)
 for f,h in pairs:obj.hide_viewport=h;obj.keyframe_insert('hide_viewport',frame=f)
for obj in list(c.objects):
 for lane in ['01','03']:
  if obj.name.startswith('HF_HP'+lane+'_'):
   c.objects.unlink(obj);bpy.data.collections['HOMI_Payment_'+lane].objects.link(obj)
bpy.data.objects['HF_Simulation'].location.z=1.29
for obj in bpy.data.objects:
 if obj.type=='FONT' and obj.name.startswith(('HF_UI','HR_UI')):obj.data.extrude=0
cam=bpy.data.objects['HOMI_Checkout_Screen'];cam.location=(-12.75,-8.58,1.72)
cam.rotation_euler=(Vector((-13.49,-8.58,1.69))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=16;cam.data.dof.use_dof=False
chip=bpy.data.objects['HR_UIReviewChip'];mat=chip.data.materials[0].copy();mat.name='HF_AnimatedStatus';chip.data.materials[0]=mat
p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
for f,color in [(1,(.95,.48,.065,1)),(679,(.95,.48,.065,1)),(680,(.7,.10,.06,1)),(859,(.7,.10,.06,1)),(860,(.95,.48,.065,1)),(1019,(.95,.48,.065,1)),(1020,(.12,.7,.53,1))]:
 for key in ['Base Color','Emission Color']:p.inputs[key].default_value=color;p.inputs[key].keyframe_insert('default_value',frame=f)
s.frame_set(740)
# Keep lane-specific details with their own station in isolated reviews.
for obj in list(c.objects):
 if 'SideSeam' in obj.name:
  bpy.data.objects.remove(obj,do_unlink=True);continue
 for lane in ['01','03']:
  if obj.name.startswith('HF_HP'+lane):
   c.objects.unlink(obj);bpy.data.collections['HOMI_Payment_'+lane].objects.link(obj)

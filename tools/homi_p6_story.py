"""Replace the visual refund story with fixture P6-01. No real payment execution.
Uses ST-1057 / RMA-1057: 200 order, 100 approved, 60 reserved,
60 attempted, 40 remaining. Run once on the current HOMI store.
"""
import bpy, math
from mathutils import Vector
s=bpy.data.scenes['Counterfoil_Market_Composite'];bpy.context.window.scene=s
if s.get('homi_p6_story'):raise RuntimeError('P6 story already applied')
def body(name,value):bpy.data.objects[name].data.body=value
for name,value in {
 'HR_UIOrder':'RETURN / ST-1057','HR_UIItem':'Cloudstone cup x4','HR_UIRecord':'APPROVED RETURN',
 'HR_UIAmount':'$100.00','HR_UIOrderTotal':'Order $200.00 / RMA-1057','HR_UIReview':'REVIEW REQUIRED',
 'HR_UIHelp':'Please wait for a team member.','HR_ReturnLabel':'01  RETURN 4 CUPS',
 'HO_QueueHeading':'RMA-1057 / REVIEW','HO_QueueAmount':'$60 requested / $40 left',
 'HO_TrustedAmount':'$100 approved / $60 reserved',
 'HF_ReceiptText2':'REFUND  $40.00','HF_ReceiptText3':'RMA-1057',
}.items():body(name,value)
for prefix in ['HP01','HP03']:
 body(prefix+'_UIItem','Cloudstone cup x8');body(prefix+'_UIAmount','$200.00');body(prefix+'_UIRecord','8 ITEMS / $25.00 EACH');body(prefix+'_UIOrder','ORDER / ST-1057')
# Customer-facing UI stays concise; internal rejection arithmetic is on the manager tablet.
states={
 620:['APPROVED RETURN','$100.00','Order $200.00 / RMA-1057','RETURN RECORD FOUND','Cloudstone cup: 4 of 8 returned.'],
 680:['APPROVED RETURN','$100.00','Order $200.00 / RMA-1057','REVIEW REQUIRED','Please wait for a team member.'],
 780:['APPROVED RETURN','$100.00','Order $200.00 / RMA-1057','REQUEST REJECTED','A corrected request is being created.'],
 860:['NEW REFUND REQUEST','$40.00','Approved $100 / reserved $60','GATEWAY RECHECK','Checking the new request again.'],
 950:['VERIFIED REQUEST','$40.00','Approved $100 / reserved $60','REFUND PROCESSING','Awaiting provider confirmation.'],
 1020:['PROVIDER CONFIRMED','$40.00','Approved $100 / prior reserved $60','REFUND COMPLETE','Collect your refund receipt.']}
for f,values in states.items():
 for tag,value in zip(['UIRecord','UIAmount','UIOrderTotal','UIReview','UIHelp'],values):body('HF_'+tag+'_'+str(f),value)
for marker in s.timeline_markers:
 if marker.frame in states:marker.name=states[marker.frame][3]
# Amber during held/rejected request; green only for the final simulated success.
p=next(n for n in bpy.data.materials['HF_AnimatedStatus'].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
for f in [1,679,680,859,860,1019]:
 for key in ['Base Color','Emission Color']:
  p.inputs[key].default_value=(.95,.48,.065,1);p.inputs[key].keyframe_insert('default_value',frame=f)
# Retire tray and obsolete belt props, including attached SKU/barcode.
for o in bpy.data.objects:
 if o.name.startswith(('HR_ReturnTray','HR_CeramicTray','HF_SKU','HF_ProductLabel','HF_Barcode','SE_Till1_Item_','SE_Till1_Receipt')):
  o.hide_render=True;o.hide_set(True)
  if o.type=='FONT' and o.name=='HF_SKU':o.data.body='CUP / ST-1057'
c=bpy.data.collections['HOMI_Return_Station']
m=bpy.data.materials.new('P6_Cloudstone_Glaze');m.use_nodes=True
p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(.63,.69,.65,1);p.inputs['Roughness'].default_value=.22
noise=m.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=180
bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.06;bump.inputs['Distance'].default_value=.0005
m.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
# Hollow ceramic body, rounded lip, interior and closed base.
profile=[(0,.006),(.052,.006),(.058,.012),(.063,.028),(.075,.165),(.074,.176),(.070,.180),(.066,.176),(.065,.166),(.054,.028),(0,.024)]
for index,(x,y) in enumerate([(-13.50,-9.93),(-13.50,-9.63),(-13.30,-9.93),(-13.30,-9.63)],1):
 verts=[];faces=[];segments=64
 for rad,z in profile:
  verts.extend((x+rad*math.cos(i*2*math.pi/segments),y+rad*math.sin(i*2*math.pi/segments),.998+z) for i in range(segments))
 for j in range(len(profile)-1):
  for i in range(segments):faces.append((j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i))
 mesh=bpy.data.meshes.new('Cloudstone cup');mesh.from_pydata(verts,[],faces);mesh.materials.append(m)
 o=bpy.data.objects.new('P6_ReturnCup_%02d'%index,mesh);c.objects.link(o)
 for poly in mesh.polygons:poly.use_smooth=True
 bpy.ops.mesh.primitive_torus_add(major_segments=40,minor_segments=12,location=(x,y+.080,1.095),major_radius=.044,minor_radius=.010,rotation=(0,math.pi/2,0))
 o=bpy.context.object;o.name='P6_CupHandle_%02d'%index
 for col in list(o.users_collection):col.objects.unlink(o)
 c.objects.link(o);o.data.materials.append(m)
 for poly in o.data.polygons:poly.use_smooth=True
# Tablet text follows its existing rig through object parenting.
screen=bpy.data.objects['Store_Manager_HandTabletScreen'];cast=bpy.data.collections['Cast_Store_Manager']
screen.data=screen.data.copy();screen.data.materials.clear();screen.data.materials.append(bpy.data.materials['HR_Screen'])
def tablet_text(name,value,y,size=.011,mat='HR_White'):
 d=bpy.data.curves.new('P6_'+name,'FONT');d.body=value;d.size=size
 o=bpy.data.objects.new('P6_Tablet_'+name,d);cast.objects.link(o);o.parent=screen;o.location=(-.122,y,.0027);d.materials.append(bpy.data.materials[mat]);return o
for name,value,y,size in [
 ('Title','HOMI / RETURN REVIEW',.074,.012),('Order','ST-1057 / RMA-1057',.054,.010),
 ('Record','Approved $100 | Reserved $60',.030,.009),('Remaining','Remaining entitlement: $40',.012,.010),
 ('Request','Requested $60  /  $20 over',-.011,.010),('Sum','$60 + $60 = $120 > $100',-.030,.010),
 ('Reason','CUMULATIVE_REFUND_EXCEEDS_RMA',-.048,.007),
 ('Rail','Order $200: below payment limit',-.063,.008),('Demo','SANDBOX / P6-01',-.084,.007)]:tablet_text(name,value,y,size)
# Tablet request/status follows the same timeline rather than showing a stale rejected amount.
req=bpy.data.objects['P6_Tablet_Request'];req.hide_render=True;req.hide_viewport=True
for a,b,txt in [(620,779,'Requested $60 / BLOCK ($20 over)'),(780,859,'Manager: reject $60 request'),(860,949,'NEW $40 request / gateway recheck'),(950,1019,'$40 sent / awaiting confirmation'),(1020,1140,'Provider confirmed $40 / receipt')]:
 o=tablet_text('State_'+str(a),txt,-.011,.009)
 for f,h in [(1,True),(a-1,True),(a,False),(b,False),(b+1,True)]:
  o.hide_render=h;o.hide_viewport=h;o.keyframe_insert('hide_render',frame=f);o.keyframe_insert('hide_viewport',frame=f)
# Update metadata so the blend does not carry obsolete numerical guidance.
s['homi_p6_story']=True
s['HOMI_checkout_note']='P6-01: ST-1057 $200, RMA-1057 $100, reserved $60, attempted $60 -> BLOCK, remaining $40. Manager rejects; fresh $40 rechecks; receipt only after simulated provider success.'
s['homi_refund_timeline']='620 RMA $100; 680 attempted $60 blocked with $60 already reserved; 780 rejected; 860 new $40 recheck; 950 pending; 1020 simulated provider confirmation; 1055 receipt.'
s.frame_set(740)
print('P6-01 screens, tablet, four hollow cups and $40 receipt updated')
# Nonreflective tablet display keeps the small physical screen readable.
m=bpy.data.materials.new('P6_Tablet_EmissiveDisplay');m.use_nodes=True
nodes=m.node_tree.nodes;nodes.clear();em=nodes.new('ShaderNodeEmission');em.inputs['Color'].default_value=(.012,.04,.033,1);em.inputs['Strength'].default_value=.7
out=nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(em.outputs[0],out.inputs[0])
screen.data.materials.clear();screen.data.materials.append(m)
bpy.data.objects['P6_Tablet_Remaining'].data.body='Available before request: $40'

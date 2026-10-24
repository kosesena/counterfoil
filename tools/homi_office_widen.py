"""Widen the existing office to 4.7 x 5.35m, moving lane 01 to the right end."""
import bpy, math
from mathutils import Vector
s=bpy.data.scenes['Counterfoil_Market_Composite'];c=bpy.data.collections['HOMI_Manager_Office']
if s.get('homi_office_wide'):raise RuntimeError('Already widened')
# Relocate complete new checkout assembly; old hidden till geometry stays preserved.
for obj in bpy.data.collections['HOMI_Payment_01'].objects:obj.location.x+=9.72
# Widen architectural shell, keeping west wall fixed.
for obj in c.objects:
 n=obj.name
 if n.startswith(('HO_Glass','HO_Mullion','HO_EastRail','HO_PrivacyStripe')):obj.location.x+=2.5
 if n in ['HO_Floor','HO_SouthWall','HO_DoorHeader']:
  obj.location.x+=1.25;obj.dimensions.x+=2.5
 if n in ['HO_DoorJamb']:obj.location.x+=2.5
 if n in ['HO_NorthGlass']:
  obj.location.x+=1.25;obj.dimensions.x+=2.5
 if n in ['HO_DoorSign']:obj.location.x+=1.25;obj.data.size=.14
 if n.startswith(('HO_Visitor','HO_SideTable','HO_Table','HO_Notebook','HO_Planter','HO_Leaf')):obj.location.x+=2.5
 if n in ['HO_Rug']:obj.location.x+=1.65;obj.dimensions.x=2.6;obj.dimensions.y=2.25
 if n in ['HO_Pendant','HO_Diffuser']:obj.location.x+=1.25
 if n.startswith(('HO_Glass','HO_NorthGlass')):obj.display_type='WIRE'
# Reduce the milky glass cast in renders.
m=bpy.data.materials['HO_Clear glass']
for n in m.node_tree.nodes:
 if n.type=='MIX_SHADER':n.inputs[0].default_value=.015
# Enlarge the workstation and add a return-inspection sideboard in the freed middle.
def box(name,loc,dims,mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name='HO_'+name
 for col in list(o.users_collection):col.objects.unlink(o)
 c.objects.link(o);o.scale=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 b=o.modifiers.new('Edges','BEVEL');b.width=.025;b.segments=3;o.data.materials.append(bpy.data.materials[mat]);return o
# Worktable return, leaving clear standing room and a wide central circulation strip.
box('ReturnWing',(-18.35,-7.6,.82),(1.4,.55,.065),'HR_Oak')
box('ReturnWingLeg',(-17.75,-7.6,.42),(.055,.43,.78),'HR_Forest')
# Separate low storage for physical returns, away from the work desk.
box('ReturnsStorage',(-18.95,-11.15,.48),(.65,1.15,.88),'HO_Warm plaster')
box('ReturnsStorageTop',(-18.95,-11.15,.94),(.72,1.22,.05),'HR_Oak')
box('InspectionTray',(-18.95,-11.12,.99),(.48,.65,.055),'HR_Forest')
for i in range(2):box('ReturnBox',(-18.95,-11.32+i*.38,1.13),(.33,.29,.23),'HR_Oak')
# Manager keeps natural scale; place beside rather than inside the guest seating area.
manager=bpy.data.objects['Inst_Store_Manager'];manager.location=(-17.9,-9.0,-.16)
# A second visitor chair faces the first across the low table.
for obj in list(c.objects):
 if obj.name.startswith(('HO_VisitorSeat','HO_VisitorBack','HO_VisitorArm')):
  dup=obj.copy();dup.data=obj.data.copy();dup.name=obj.name+'_Second';c.objects.link(dup)
  dup.location.x=2*(-15.8)-obj.location.x;dup.location.y-=.1
# Move second chair inward to retain clearance at the glass.
for obj in c.objects:
 if obj.name.endswith('_Second'):obj.location.x-=.55
cam=bpy.data.objects['HOMI_Office_Camera'];cam.location=(-9.0,-2.7,7.4);target=Vector((-17.15,-9.65,1.2));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=9.0
for name,loc in [('HO_Key',(-14,-7,6)),('HO_Fill',(-17,-10,3.5))]:
 obj=bpy.data.objects[name];obj.location=loc;obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
s['homi_office_wide']=True;s['homi_office_area_m2']=25.145
r=bpy.data.scenes['HOMI_Office_Review'];bpy.context.window.scene=r;r.frame_end=1140;r.frame_set(740);r.render.filepath='/Users/kosesena/Documents/Codex/2026-10-23/se/outputs/homi-office-wide.png'
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':
  area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.region_3d.view_camera_zoom=0;area.spaces.active.overlay.show_overlays=False
# Reframe three-lane comparison after lane 01 relocation.
cam=bpy.data.objects['HOMI_Three_Checkouts_Camera'];cam.location.x+=3.2
cam.rotation_euler=(Vector((-10.23,-8.65,1.15))-cam.location).to_track_quat('-Z','Y').to_euler()
print('Office 25.145 m2; lane 01 moved +9.72m along checkout row')
# Keep visitor seats and table separated in the larger lounge area.
for obj in c.objects:
 if obj.name.startswith(('HO_VisitorSeat','HO_VisitorBack','HO_VisitorArm')):obj.location.x+=.2 if obj.name.endswith('_Second') else -.45
 if obj.name in ['HO_SideTable','HO_TableStem','HO_TableBase','HO_Notebook']:obj.location.x-=.47;obj.location.y+=.28
bpy.data.objects['HO_Rug'].location.x=-16.2

"""Enlarge HOMI's manager office into the unused west-side strip. Run once."""
import bpy, math
from mathutils import Vector
s=bpy.data.scenes['Counterfoil_Market_Composite'];bpy.context.window.scene=s
if bpy.data.collections.get('HOMI_Manager_Office'):raise RuntimeError('Office already built')
c=bpy.data.collections.new('HOMI_Manager_Office');s.collection.children.link(c)
for o in s.objects:
 if o.name.startswith('SE_Office_'):o.hide_render=True;o.hide_set(True)
def mat(name,color,rough=.5):
 m=bpy.data.materials.new('HO_'+name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
 return m
cream=mat('Warm plaster',(.72,.70,.61));fabric=mat('Sage upholstery',(.17,.28,.23),.85);rug=mat('Woven rug',(.36,.34,.29),.95)
wood=bpy.data.materials['HR_Oak'];dark=bpy.data.materials['HR_Forest'];ink=bpy.data.materials['HR_Ink'];white=bpy.data.materials['HR_White'];steel=bpy.data.materials['HR_Steel'];teal=bpy.data.materials['HR_Teal']
glass=mat('Clear glass',(.65,.86,.83),.1)
n=glass.node_tree.nodes;l=glass.node_tree.links;out=next(v for v in n if v.type=='OUTPUT_MATERIAL');p=next(v for v in n if v.type=='BSDF_PRINCIPLED');tr=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=.07;l.new(tr.outputs[0],mix.inputs[1]);l.new(p.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs[0])
def adopt(o,name,m):
 o.name='HO_'+name
 for col in list(o.users_collection):col.objects.unlink(o)
 c.objects.link(o);o.data.materials.append(m);return o
def box(name,loc,dims,m,r=.015):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=adopt(bpy.context.object,name,m);o.scale=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 b=o.modifiers.new('Soft edges','BEVEL');b.width=r;b.segments=3;o.modifiers.new('Normals','WEIGHTED_NORMAL');return o
def cyl(name,loc,r,depth,m):
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=depth,location=loc);return adopt(bpy.context.object,name,m)
def text(name,body,loc,size,m=white,face='x'):
 d=bpy.data.curves.new(name,'FONT');d.body=body;d.size=size;d.align_x='CENTER'
 o=bpy.data.objects.new('HO_'+name,d);c.objects.link(o);o.location=loc;o.rotation_euler=(math.pi/2,0,math.pi/2 if face=='x' else math.pi);d.materials.append(m);return o
# 2.2 x 5.35 m; stays inside exterior facade and behind lane 01.
box('Floor',(-18.4,-9.675,.025),(2.20,5.35,.05),wood)
box('WestWall',(-19.5,-9.675,1.55),(.065,5.35,3.1),cream)
box('SouthWall',(-18.4,-12.35,1.55),(2.2,.065,3.1),cream)
for yy in [-12.35,-10.55,-8.75,-7.0]:
 box('Mullion',(-17.3,yy,1.55),(.045,.045,3.1),dark,.006)
for yy in [-11.45,-9.65,-7.875]:
 box('Glass',(-17.3,yy,1.55),(.012,1.72,3.02),glass,.001)
for z in [.10,3.08]:box('EastRail',(-17.3,-9.675,z),(.05,5.35,.05),dark,.005)
# North entrance with an unobstructed 0.95 m doorway.
box('DoorHeader',(-18.4,-7,2.9),(2.2,.06,.3),dark)
box('DoorJamb',(-18.3,-7,1.35),(.045,.05,2.7),dark)
box('NorthGlass',(-18.93,-7,1.35),(1.10,.012,2.7),glass)
text('DoorSign','HOMI  /  OPERATIONS',(-18.4,-6.96,2.84),.095,white,'y')
for yy in [-11.4,-9.6,-7.85]:
 box('PrivacyStripe',(-17.288,yy,1.05),(.004,1.6,.12),cream,.001)
# Long workstation against west wall, dual monitors facing into room.
box('Desk',(-19.05,-8.55,.82),(.78,2.30,.065),wood,.035)
for yy in [-9.55,-7.55]:box('DeskFrame',(-19.05,yy,.42),(.64,.055,.79),dark)
box('DrawerUnit',(-19.05,-9.28,.4),(.65,.55,.75),cream,.025)
for z in [.2,.44,.66]:box('DrawerHandle',(-18.715,-9.28,z),(.025,.18,.02),steel,.005)
for yy in [-8.75,-7.98]:
 box('MonitorFoot',(-19.1,yy,.88),(.23,.35,.035),dark)
 box('MonitorStem',(-19.2,yy,1.04),(.04,.05,.30),steel)
 box('Monitor',(-19.2,yy,1.28),(.055,.66,.43),ink,.025)
 box('MonitorDisplay',(-19.169,yy,1.28),(.006,.61,.37),dark,.008)
text('QueueHeading','RETURN REVIEW',(-19.163,-8.75,1.38),.045)
text('QueueAmount','$90 requested',(-19.163,-8.75,1.27),.043)
text('TrustedAmount','RMA: $30',(-19.163,-8.75,1.17),.04,teal)
text('SecondHeading','STORE ACTIVITY',(-19.163,-7.98,1.38),.04)
for i in range(4):box('DashboardBar',(-19.16,-8.17+i*.12,1.22),(.005,.06,.08+i*.025),teal,.002)
box('Keyboard',(-18.84,-8.70,.868),(.18,.46,.025),ink,.01)
for row in range(4):
 for k in range(11):box('Key',(-18.90+row*.04,-8.90+k*.039,.884),(.025,.026,.007),steel,.002)
box('Mousepad',(-18.83,-8.27,.858),(.24,.22,.008),fabric)
box('Mouse',(-18.83,-8.27,.88),(.09,.055,.035),cream,.02)
cyl('Mug',(-18.85,-7.64,.91),.045,.10,cream)
# Office chair, behind the manager's standing review position.
cyl('ChairBase',(-17.91,-8.0,.11),.27,.035,ink)
cyl('ChairPiston',(-17.91,-8,.30),.035,.38,steel)
box('ChairSeat',(-17.91,-8,.53),(.48,.48,.12),fabric,.06)
box('ChairBack',(-17.64,-8,.88),(.09,.48,.62),fabric,.05)
for yy in [-8.26,-7.74]:box('ChairArm',(-17.91,yy,.75),(.40,.05,.06),dark)
# Filing and printer station at south end.
box('Cabinet',(-18.45,-12.08,.53),(1.75,.48,1.0),cream,.025)
for xx in [-18.88,-18.02]:
 box('CabinetDoor',(xx,-11.825,.53),(.83,.025,.90),wood,.008)
 box('CabinetPull',(xx+.28,-11.805,.57),(.025,.025,.18),steel,.005)
box('Printer',(-18.87,-12.05,1.18),(.55,.36,.25),ink,.03)
box('PrinterPaper',(-18.87,-11.86,1.23),(.32,.12,.015),white,.003)
for i in range(6):box('Binder',(-18.2+i*.085,-12.05,1.20),(.065,.27,.34),dark if i%2 else fabric,.004)
box('Shelf',(-18.4,-12.12,1.84),(1.7,.35,.045),wood)
text('Archive','HOMI / RECORDS',(-18.4,-12.30,2.16),.10,dark,'y')
# Visitor seat, side table, rug, and a tall plant.
box('Rug',(-18.4,-10.65,.065),(1.70,1.5,.015),rug,.025)
box('VisitorSeat',(-19.05,-10.8,.45),(.60,.65,.20),fabric,.08)
box('VisitorBack',(-19.32,-10.8,.78),(.12,.65,.60),fabric,.06)
for yy in [-11.14,-10.46]:box('VisitorArm',(-19.05,yy,.64),(.58,.09,.24),fabric,.04)
cyl('SideTable',(-18.23,-11.08,.53),.27,.045,wood);cyl('TableStem',(-18.23,-11.08,.29),.045,.46,dark);cyl('TableBase',(-18.23,-11.08,.08),.19,.025,dark)
box('Notebook',(-18.23,-11.08,.56),(.24,.16,.025),cream,.005)
cyl('Planter',(-17.63,-11.99,.24),.19,.43,cream)
for i in range(11):
 angle=i*2.4;height=.5+(i%4)*.17
 bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,location=(-17.63+.12*math.cos(angle),-11.99+.12*math.sin(angle),.35+height/2))
 o=adopt(bpy.context.object,'Leaf',fabric);o.scale=(.055,.10,height*.65);o.rotation_euler=(.25*math.cos(angle),.30*math.sin(angle),angle)
# Linear light; open ceiling keeps camera views readable.
box('Pendant',(-18.4,-9.4,2.85),(.12,2.0,.065),dark)
box('Diffuser',(-18.4,-9.4,2.81),(.095,1.95,.012),white)
manager=bpy.data.objects['Inst_Store_Manager'];manager.location=(-18.0,-9.65,-.16);manager.rotation_euler.z=-math.pi/2
# Dedicated review view shares the actual office and manager instance.
r=bpy.data.scenes.new('HOMI_Office_Review');r.collection.children.link(c);r.collection.objects.link(manager);r.world=bpy.data.scenes['HOMI_Checkout_Design_Review'].world;r.render.engine=s.render.engine
camdata=bpy.data.cameras.new('HOMI_Office_Camera');cam=bpy.data.objects.new('HOMI_Office_Camera',camdata);r.collection.objects.link(cam);s.collection.objects.link(cam)
cam.location=(-11.7,-3.0,6.1);target=Vector((-18.4,-9.65,1.2));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camdata.type='ORTHO';camdata.ortho_scale=7.7;r.camera=cam
for name,loc,power,size in [('Key',(-15,-7,6),1000,5),('Fill',(-18,-10,3.5),350,3)]:
 d=bpy.data.lights.new('HO_'+name,'AREA');d.energy=power;d.size=size;o=bpy.data.objects.new('HO_'+name,d);c.objects.link(o);o.location=loc;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
r.frame_set(740);r.render.resolution_x=2560;r.render.resolution_y=1920;r.render.resolution_percentage=50;r.render.filepath='/Users/kosesena/Documents/Codex/2026-10-23/se/outputs/homi-office-preview.png'
bpy.context.window.scene=r
print('Built 11.77 square metre office; old office hidden; checkout and exit gate geometry unchanged')

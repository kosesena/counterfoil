"""Build the HOMI Till1 self-service return station in the open store file.
Visual prototype only: no payment/backend integration or success claim.
Original Till1 and agent instances are hidden, not deleted. No git operations.
"""
import bpy, math
from mathutils import Vector

s = bpy.data.scenes['Counterfoil_Market_Composite']
bpy.context.window.scene = s
if bpy.data.collections.get('HOMI_Return_Station'):
    raise RuntimeError('Station already exists; do not duplicate it')
c = bpy.data.collections.new('HOMI_Return_Station')
s.collection.children.link(c)
for o in s.objects:
    if o.name.startswith('SE_Till1_') or o.name in ('Inst_Reader_Agent', 'Inst_Transaction_Agent'):
        o.hide_render = True
        o.hide_set(True)

def material(name, color, metallic=0, rough=.4, emission=0):
    m=bpy.data.materials.new('HR_'+name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metallic;p.inputs['Roughness'].default_value=rough
    if emission:
        p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    return m
ivory=material('Porcelain',(.83,.81,.72))
green=material('Forest',(.025,.12,.085))
oak=material('Oak',(.52,.31,.13),rough=.5)
ink=material('Ink',(.012,.025,.026))
white=material('White',(.93,.95,.90),emission=.2)
screen=material('Screen',(.025,.07,.065),rough=.25)
teal=material('Teal',(.12,.7,.53),emission=.45)
amber=material('Amber',(.95,.48,.065),emission=.3)
steel=material('Steel',(.45,.49,.48),.75,.25)
ceramic=material('Ceramic',(.75,.61,.42),rough=.28)
# Subtle elongated grain on real geometry, no external textures.
nodes=oak.node_tree.nodes;links=oak.node_tree.links
tex=nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=4;tex.inputs['Detail'].default_value=2
coord=nodes.new('ShaderNodeTexCoord');mapping=nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(4,4,65)
links.new(coord.outputs['Generated'],mapping.inputs[0]);links.new(mapping.outputs[0],tex.inputs['Vector'])
ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.27,.13,.045,1);ramp.color_ramp.elements[1].color=(.67,.46,.24,1)
links.new(tex.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs[0],next(n for n in nodes if n.type=='BSDF_PRINCIPLED').inputs['Base Color'])

# Local u is across the counter; d is depth away from the customer (+world x).
def pos(u,d,z): return (-13.47-d,-8.65+u,z)
def adopt(o,name,m):
    o.name='HR_'+name
    for col in list(o.users_collection):col.objects.unlink(o)
    c.objects.link(o);o.data.materials.append(m)
    return o
def box(name,u,d,z,w,depth,h,m,b=.015):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos(u,d,z));o=adopt(bpy.context.object,name,m)
    o.scale=(depth,w,h);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    mod=o.modifiers.new('Manufactured radius','BEVEL');mod.width=b;mod.segments=4
    o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return o
def text(name,body,u,d,z,size,m=white,align='LEFT'):
    cu=bpy.data.curves.new('HR_'+name,'FONT');cu.body=body;cu.size=size;cu.align_x=align;cu.extrude=.00015
    o=bpy.data.objects.new('HR_'+name,cu);c.objects.link(o);cu.materials.append(m)
    o.location=pos(u,d,z);o.rotation_euler=(math.pi/2,0,math.pi/2);return o
def sphere(name,u,d,z,scale,m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=pos(u,d,z));o=adopt(bpy.context.object,name,m);o.scale=scale
    for p in o.data.polygons:p.use_smooth=True
    return o

# Same lane footprint: rounded lower case, accessible approach and two distinct surfaces.
box('ToeKick',0,.02,.065,2.12,.66,.13,ink,.035)
box('Cabinet',0,.02,.48,2.18,.72,.82,ivory,.075)
box('Top',0,0,.93,2.30,.82,.08,ivory,.035)
box('OakFront',0,-.35,.49,2.04,.035,.69,oak,.012)
for i in range(35):
    box('FrontFlute_%02d'%i,-.985+i*.058,-.376,.49,.012,.012,.66,green,.004)
box('BrandPlaque',0,-.392,.58,.57,.022,.19,green,.03)
text('HOMI','HOMI',0,-.407,.545,.115,white,'CENTER')
text('FrontService','SELF-SERVICE RETURNS',0,-.409,.36,.036,green,'CENTER')

# Product landing tray on the left, separate collection pad on the right.
box('ReturnPad',-.79,-.04,.983,.61,.58,.025,green,.025)
box('ReturnTrayBase',-.79,-.04,1.012,.43,.31,.025,ceramic,.045)
for u,d,w,dep in [(-.79,-.185,.43,.02),(-.79,.105,.43,.02),(-.995,-.04,.02,.29),(-.585,-.04,.02,.29)]:
    box('CeramicTrayRim',u,d,1.033,w,dep,.035,ceramic,.01)
text('ReturnLabel','01  RETURN ITEM',-.79,-.428,.85,.029,green,'CENTER')
box('CollectionPad',.83,.02,.985,.48,.53,.018,oak,.025)
text('CollectLabel','03  RECEIPT',.82,-.428,.85,.029,green,'CENTER')

# Central customer-facing kiosk; screen normal points toward the final customer position.
box('KioskPedestal',.05,.14,1.08,.28,.23,.25,green,.03)
box('KioskShell',.05,.13,1.54,.78,.15,.80,green,.055)
box('ScreenBezel',.05,.043,1.55,.71,.026,.69,ink,.035)
box('ScreenGlass',.05,.025,1.55,.65,.008,.63,screen,.02)
text('UIBrand','HOMI',-.23,.017,1.81,.047)
text('UIOrder','RETURN  /  ST-1042',-.23,.017,1.75,.025)
text('UIItem','Ceramic tray',-.23,.017,1.67,.035)
text('UIRecord','STORE-VERIFIED RETURN',-.23,.017,1.61,.019,teal)
text('UIAmount','$30.00',-.23,.017,1.515,.077)
text('UIOrderTotal','Original order: $90.00',-.23,.017,1.465,.023)
box('UIReviewChip',.05,.013,1.39,.55,.005,.075,amber,.01)
text('UIReview','REVIEW IN PROGRESS',.05,.008,1.38,.024,ink,'CENTER')
text('UIHelp','A team member will check your return.',-.23,.017,1.315,.017)
text('UIDigitalAgent','AI transaction assistant',-.23,.017,1.27,.019,teal)
# Small agent avatar on-screen, not a second physical cashier.
box('AgentAvatar',.25,.008,1.79,.10,.008,.075,teal,.018)
for u in [.23,.27]:sphere('AvatarEye',u,-.001,1.80,(.005,.006,.007),ink)

# Reader: compact document scanner, status bar and lens beside return pad.
box('ReaderFoot',-.76,.26,1.00,.30,.22,.055,steel,.025)
box('ReaderStem',-.76,.29,1.17,.065,.065,.31,green,.015)
box('ReaderHead',-.76,.19,1.35,.29,.20,.19,ivory,.04)
box('ReaderFace',-.76,.082,1.35,.24,.02,.13,ink,.02)
sphere('ReaderLens',-.76,.064,1.35,(.018,.038,.038),steel)
sphere('ReaderLensGlass',-.76,.047,1.35,(.009,.025,.025),screen)
box('ReaderStatus',-.76,.065,1.40,.15,.005,.009,teal,.003)
text('ReaderLabel','AI READER',-.76,.065,1.255,.027,green,'CENTER')
text('ScannerInstruction','SCAN RECEIPT / QR',-.77,-.428,.79,.022,green,'CENTER')

# Payment terminal with screen, card slot, contactless marker and physical keys.
box('POSStand',.79,.03,1.08,.10,.14,.18,steel,.02)
box('POSBody',.79,-.005,1.25,.24,.095,.33,ink,.025)
box('POSDisplay',.79,-.059,1.31,.195,.009,.16,screen,.01)
text('POSCaption','PAYMENT',.79,-.067,1.34,.024,white,'CENTER')
text('POSWait','WAITING',.79,-.067,1.29,.022,teal,'CENTER')
for r in range(3):
    for k in range(3):box('POSKey',.73+k*.06,-.063,1.19-r*.025,.04,.009,.016,steel,.004)
box('CardSlot',.79,-.060,1.10,.15,.009,.008,steel,.003)
text('POSContactless',')))',.79,-.067,1.235,.025,white,'CENTER')
# Closed printer slot: no successful refund receipt before provider confirmation.
box('PrinterFace',.78,-.38,.69,.30,.025,.18,ivory,.02)
box('PrinterSlot',.78,-.398,.71,.21,.009,.014,ink,.004)
text('PrinterLabel','RECEIPT',.78,-.4,.64,.025,green,'CENTER')

# Lane marker and a small, honest security status strip.
box('LaneSignPost',1.03,.30,1.73,.035,.035,1.50,steel,.009)
box('LaneSign',.82,.30,2.42,.48,.055,.34,green,.04)
text('LaneNumber','02',.82,.267,2.43,.14,white,'CENTER')
text('LaneTitle','RETURNS',.82,.267,2.32,.036,white,'CENTER')
text('CounterfoilLabel','Protected by Counterfoil',.03,-.409,.24,.025,green,'CENTER')
box('StatusBar',0,-.373,.91,2.00,.018,.012,amber,.004)

# Two saved camera angles; maintain all existing camera and walking keyframes.
def camera(name,loc,target,lens):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);s.collection.objects.link(o)
    o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;return o
hero=camera('HOMI_Checkout_Hero',(-10.0,-11.4,2.55),(-13.47,-8.60,1.16),48)
detail=camera('HOMI_Checkout_Screen',(-11.8,-8.72,1.63),(-13.48,-8.60,1.55),58)
for name,loc,power,size in [('Key',(-11,-10,4),180,3),('Fill',(-12,-6,3),110,2)]:
    d=bpy.data.lights.new('HR_'+name,'AREA');d.energy=power;d.size=size
    o=bpy.data.objects.new('HR_'+name,d);c.objects.link(o);o.location=loc
    o.rotation_euler=(Vector((-13.47,-8.6,1))-o.location).to_track_quat('-Z','Y').to_euler()
s.camera=hero;s.frame_set(620)
s['HOMI_checkout_note']='Visual review state only. Reject $90; create fresh $30 request; verify provider success before receipt. No backend connection.'
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
print('Created HOMI return station:',len(c.objects),'objects')

"""Enlarge the existing HOMI station for the demo's hero scene; apply once."""
import bpy, math
from mathutils import Vector
s=bpy.data.scenes['Counterfoil_Market_Composite']
c=bpy.data.collections['HOMI_Return_Station']
if s.get('homi_large_station'):
    raise RuntimeError('Large station is already applied')
screen_prefixes=('Kiosk','Screen','UI','AgentAvatar','AvatarEye')
fixed_prefixes=('ReturnTray','CeramicTray','Reader','POS')
for o in list(c.objects):
    if o.type=='LIGHT': continue
    tag=o.name.removeprefix('HR_')
    u=o.location.y+8.65
    o.location.y=-8.65+u*1.42
    if tag.startswith(screen_prefixes):
        # All screen elements use a coherent transform around the screen base.
        o.location.z=1.0+(o.location.z-1.0)*1.25
        if o.type=='FONT': o.scale*=1.25
        else:
            o.scale.y*=1.42;o.scale.z*=1.25
    elif tag.startswith(fixed_prefixes):
        pass
    elif o.type=='FONT':
        o.scale*=1.15
    else:
        o.scale.y*=1.42

# Make the review state legible without dense explanatory microcopy.
bpy.data.objects['HR_UIHelp'].data.body='Please wait for a team member.'
bpy.data.objects['HR_UIRecord'].data.body='APPROVED RETURN'
bpy.data.objects['HR_UIOrderTotal'].data.body='Order total  $90.00'
bpy.data.objects['HR_UIDigitalAgent'].data.body='AI assistant  /  Counterfoil'

def pt(u,d,z):return (-13.47-d,-8.65+u,z)
def box(name,u,d,z,w,dep,h,mat):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pt(u,d,z));o=bpy.context.object;o.name='HR_'+name
    for col in list(o.users_collection):col.objects.unlink(o)
    c.objects.link(o);o.scale=(dep,w,h);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    b=o.modifiers.new('Rounded','BEVEL');b.width=.012;b.segments=3;o.modifiers.new('Normals','WEIGHTED_NORMAL');o.data.materials.append(mat);return o
def text(name,body,u,d,z,size):
    cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.align_x='CENTER';cu.extrude=.0001
    o=bpy.data.objects.new('HR_'+name,cu);c.objects.link(o);o.location=pt(u,d,z);o.rotation_euler=(math.pi/2,0,math.pi/2);cu.materials.append(bpy.data.materials['HR_Forest']);return o

# Reuse the supplied unchanged official logo material on a distinct payment-method card.
box('PayPalAcceptanceBacking',1.14,-.38,.47,.48,.03,.19,bpy.data.materials['HR_White'])
img=bpy.data.images.load('/Users/kosesena/Desktop/paypal-ai-hackathon/marka-dis/paypal-2024/black/Logo - Black/PayPal-Logo-Black-RGB.png',check_existing=True)
ratio=img.size[0]/img.size[1]
w=.31;h=w/ratio
bpy.ops.mesh.primitive_plane_add(size=1,location=pt(1.14,-.398,.49));o=bpy.context.object;o.name='HR_PayPalAcceptanceLogo'
for col in list(o.users_collection):col.objects.unlink(o)
c.objects.link(o);o.rotation_euler=(math.pi/2,0,math.pi/2);o.scale=(w,h,1);o.data.materials.append(bpy.data.materials['PP_Word_OnWhite'])
text('SandboxLabel','SANDBOX DEMO',1.14,-.400,.408,.022)
s['homi_large_station']=True
s['logo_note']='Official supplied PayPal artwork, unmodified. 3D/video use permission not verified; separate HR_PayPal* objects for removal.'
hero=bpy.data.objects['HOMI_Checkout_Hero'];hero.location=(-9.3,-5.25,2.85);hero.rotation_euler=(Vector((-13.3,-8.6,1.25))-hero.location).to_track_quat('-Z','Y').to_euler();hero.data.lens=38
detail=bpy.data.objects['HOMI_Checkout_Screen'];detail.location=(-11.6,-8.8,1.85);detail.rotation_euler=(Vector((-13.49,-8.58,1.69))-detail.location).to_track_quat('-Z','Y').to_euler();detail.data.lens=46
review=bpy.data.scenes['HOMI_Checkout_Design_Review'];review.camera.data.ortho_scale=4.75
review.camera.rotation_euler=(Vector((-13.47,-8.60,1.30))-review.camera.location).to_track_quat('-Z','Y').to_euler()
review.render.resolution_x=3840;review.render.resolution_y=2560
review.render.filepath='/Users/kosesena/Documents/Codex/2026-10-23/se/outputs/homi-self-service-design-4k.png'
s.render.resolution_x=3840;s.render.resolution_y=2160
s.render.filepath='/Users/kosesena/Documents/Codex/2026-10-23/se/outputs/homi-self-service-in-store-4k.png'
print('Station widened to 3.27 m; larger screen; official PayPal payment-method card added')

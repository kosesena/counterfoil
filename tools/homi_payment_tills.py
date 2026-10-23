"""Match lanes 01/03 to HOMI's existing return station. Run once in Blender."""
import bpy
from mathutils import Vector
s=bpy.data.scenes['Counterfoil_Market_Composite']
src=bpy.data.collections['HOMI_Return_Station']
if bpy.data.collections.get('HOMI_Payment_01'):
    raise RuntimeError('Payment lanes already exist')
skip=('Reader','ReturnTray','CeramicTray','ScannerInstruction','Key','Fill')
copycols=[]
for idx,label in [(0,'01'),(2,'03')]:
    anchor=bpy.data.objects[f'SE_Till{idx}_Body'].location.x
    col=bpy.data.collections.new('HOMI_Payment_'+label);s.collection.children.link(col);copycols.append(col)
    for old in list(s.objects):
        if old.name.startswith(f'SE_Till{idx}_'):
            old.hide_render=True;old.hide_set(True)
    for original in list(src.objects):
        tag=original.name.removeprefix('HR_')
        if original.type=='LIGHT' or tag.startswith(skip):continue
        o=original.copy()
        if original.data:o.data=original.data.copy()
        o.name='HP'+label+'_'+tag;col.objects.link(o)
        o.location.x+=anchor+13.47
        o.location.y=-8.65+(original.location.y+8.65)*.74
        if o.type=='FONT':o.scale*=.78
        else:o.scale.y*=.74
        if tag.startswith(('Kiosk','Screen','UI','AgentAvatar','AvatarEye')):
            o.location.z=1+(original.location.z-1)*.86
            if o.type!='FONT':o.scale.z*=.86
        if o.type=='FONT':
            replacements={
                'LaneNumber':label,'LaneTitle':'CHECKOUT',
                'FrontService':'SELF-SERVICE CHECKOUT',
                'ReturnLabel':'01  SCAN ITEMS','CollectLabel':'03  COLLECT RECEIPT',
                'UIOrder':'YOUR SHOPPING BAG','UIItem':'Tray / Bowl / Vase',
                'UIRecord':'3 ITEMS','UIAmount':'$90.00',
                'UIOrderTotal':'Choose your payment method',
                'UIReview':'READY TO PAY','UIHelp':'Review your items, then pay.',
                'UIDigitalAgent':'AI checkout assistant',
                'POSWait':'READY',
            }
            if tag in replacements:o.data.body=replacements[tag]
        if tag=='UIReviewChip':
            o.data.materials.clear();o.data.materials.append(bpy.data.materials['HR_Teal'])
        if tag=='ReturnPad':
            o.name='HP'+label+'_ScannerWindow';o.data.materials.clear();o.data.materials.append(bpy.data.materials['HR_Ink'])
    # Flush glass scan window rather than a reader robot; laser strip sits above it.
    glass=bpy.data.objects['HP'+label+'_ScannerWindow']
    strip=glass.copy();strip.data=glass.data.copy();strip.name='HP'+label+'_ScannerLight';col.objects.link(strip)
    strip.scale.y*=.78;strip.scale.x*=.025;strip.location.z+=.015
    strip.data.materials.clear();strip.data.materials.append(bpy.data.materials['HR_Teal'])

# Product-review scene shows all three lanes without walls obstructing the comparison.
review=bpy.data.scenes.new('HOMI_Three_Checkouts_Review')
for col in [src]+copycols:review.collection.children.link(col)
review.world=bpy.data.scenes['HOMI_Checkout_Design_Review'].world
floor=bpy.data.objects['HOMI_Review_Floor'];review.collection.objects.link(floor)
d=bpy.data.cameras.new('HOMI_Three_Checkouts_Camera');cam=bpy.data.objects.new('HOMI_Three_Checkouts_Camera',d);review.collection.objects.link(cam)
cam.location=(-6,-15,7);cam.rotation_euler=(Vector((-13.47,-8.65,1.15))-cam.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=10.5
review.camera=cam;review.render.engine=s.render.engine
review.render.resolution_x=3840;review.render.resolution_y=2160;review.render.resolution_percentage=100
review.render.image_settings.file_format='PNG';review.render.filepath='/Users/kosesena/Documents/Codex/2026-10-23/se/outputs/homi-three-checkouts-4k.png'
for name,loc,power,size in [('AllKey',(-10,-12,7),1300,8),('AllFill',(-18,-5,6),1000,6)]:
    light=bpy.data.lights.new('HP_'+name,'AREA');light.energy=power;light.size=size
    ob=bpy.data.objects.new('HP_'+name,light);review.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((-13.47,-8.65,1))-ob.location).to_track_quat('-Z','Y').to_euler()
s['homi_payment_lanes']='01 and 03: compact self-service payment. 02: larger return station. Static UI design.'
print('Created matching payment lanes 01 and 03; lane 02 unchanged')

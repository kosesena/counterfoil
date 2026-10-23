"""Add docked handheld and vertical barcode readers to the three HOMI lanes.
Run in the existing Blender store. Geometry only; no scanning integration.
Safe to rerun: replaces only HS_ objects.
"""
import bpy, math
from mathutils import Vector

for obj in list(bpy.data.objects):
    if obj.name.startswith('HS_'):
        bpy.data.objects.remove(obj, do_unlink=True)

def box(name, loc, dims, mat, radius=.015):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj=bpy.context.object; obj.name='HS_'+lane+'_'+name
    for c in list(obj.users_collection): c.objects.unlink(obj)
    col.objects.link(obj); obj.scale=dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel=obj.modifiers.new('Moulded edges','BEVEL'); bevel.width=radius; bevel.segments=5
    obj.modifiers.new('Normals','WEIGHTED_NORMAL')
    obj.data.materials.append(bpy.data.materials['HR_'+mat])
    return obj

for lane, collection, pad in [('01','HOMI_Payment_01','HP01_ScannerWindow'),('02','HOMI_Return_Station','HR_ReturnPad'),('03','HOMI_Payment_03','HP03_ScannerWindow')]:
    col=bpy.data.collections[collection]
    x,y,z=bpy.data.objects[pad].location
    # Vertical window immediately behind the flat scanner / returned product.
    box('VerticalFoot',(x-.24,y,1.005),(.18,.36,.055),'Forest')
    box('VerticalHousing',(x-.25,y,1.22),(.12,.33,.43),'Porcelain',.035)
    box('VerticalBezel',(x-.183,y,1.24),(.025,.275,.30),'Ink',.022)
    box('VerticalGlass',(x-.168,y,1.24),(.008,.235,.255),'Screen',.016)
    box('StatusLED',(x-.161,y,1.40),(.006,.13,.008),'Teal',.003)
    for side in [-1,1]:
        box('ScanGuide'+str(side),(x-.161,y+side*.075,1.24),(.006,.008,.10),'Teal',.002)
    # Removable wireless reader in a weighted charging cradle beside the pad.
    hx,hy=x+.14,y+.31
    box('Dock',(hx,hy,1.015),(.18,.12,.07),'Forest',.02)
    grip=box('HandGrip',(hx-.025,hy,1.16),(.08,.068,.26),'Ink',.025)
    grip.rotation_euler.y=-.22
    box('Trigger',(hx+.021,hy,1.21),(.018,.042,.055),'Teal',.008)
    box('HandHead',(hx-.055,hy,1.315),(.19,.115,.105),'Porcelain',.025)
    box('HandWindow',(hx+.045,hy,1.315),(.012,.083,.065),'Ink',.01)
    box('HandLens',(hx+.052,hy,1.315),(.004,.059,.038),'Screen',.006)
    box('DockIndicator',(hx+.092,hy,1.02),(.004,.035,.007),'Teal',.002)

# Replace the former camera-shaped reader with the new receipt/barcode reader.
for obj in bpy.data.collections['HOMI_Return_Station'].objects:
    if obj.name.startswith('HR_Reader'):
        obj.hide_render=True; obj.hide_set(True)
bpy.data.objects['HR_ScannerInstruction'].data.body='SCAN RECEIPT / BARCODE'
review=bpy.data.scenes['HOMI_Three_Checkouts_Review']
review.camera.data.ortho_scale=11.5
bpy.context.window.scene=review
review['scanner_note']='Static dual-window barcode readers and wireless handhelds. Animation/backend not connected.'
print('Added vertical and docked handheld readers on lanes 01, 02, 03')

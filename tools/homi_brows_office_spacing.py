"""Flush eyebrow ribbons and office setback; keep manager/tablet choreography aligned."""
import bpy,math
from mathutils import Vector
s=bpy.data.scenes['Counterfoil_Market_Composite']
if s.get('homi_brows_office_spacing'):raise RuntimeError('Already applied')
for role,cx in [('Customer',-3.6),('Store_Manager',-1.2)]:
 for side in ['1','-1']:
  old=bpy.data.objects[role+'_Brow'+side];pts=list(old.data.splines[0].points);x0=pts[0].co.x;x1=pts[-1].co.x;verts=[];faces=[]
  for i in range(17):
   t=i/16;x=x0+(x1-x0)*t;z=2.535+.012*math.sin(math.pi*t)
   for dz in [-.006,.006]:
    zz=z+dz;y=-math.sqrt(max(.001,.36**2-(x-cx)**2-(zz-2.42)**2))-.002
    verts.append((x,y,zz))
  for i in range(16):faces.append((2*i,2*i+1,2*i+3,2*i+2))
  mesh=bpy.data.meshes.new(old.name+'_FlushRibbon');mesh.from_pydata(verts,[],faces);mesh.materials.append(old.data.materials[0])
  new=bpy.data.objects.new(old.name+'_New',mesh)
  for col in old.users_collection:col.objects.link(new)
  new.parent=old.parent;new.parent_type=old.parent_type;new.parent_bone=old.parent_bone;new.matrix_parent_inverse=old.matrix_parent_inverse.copy();new.matrix_basis=old.matrix_basis.copy();name=old.name
  bpy.data.objects.remove(old,do_unlink=True);new.name=name
# Set room back along existing empty left-side strip; shelves start beyond -3.18Y.
delta=Vector((0,3.5,0));objects=set(bpy.data.collections['HOMI_Manager_Office'].objects)
objects.add(bpy.data.objects['Inst_Store_Manager'])
for o in bpy.data.objects:
 if o.name.startswith(('PC_Store_Manager','PC_Manager')) or o.name=='HOMI_Office_Camera':objects.add(o)
for o in objects:
 if o.parent and o.parent in objects:continue
 o.location+=delta
 action=o.animation_data.action if o.animation_data else None
 if action:
  for layer in action.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      if fc.data_path=='location' and fc.array_index==1:
       for kp in fc.keyframe_points:
        kp.co.y+=3.5;kp.handle_left.y+=3.5;kp.handle_right.y+=3.5
s['homi_brows_office_spacing']='Flat curved eyebrow ribbons; office, manager and manager choreography moved 3.5m towards back of store.'
r=bpy.data.scenes['HOMI_P6_Scan_Review'];bpy.context.window.scene=r;r.frame_set(646);r.camera=bpy.data.objects['PC_ScanCamera'];r.render.filepath='/Users/kosesena/Documents/Codex/2026-10-23/se/outputs/homi-flat-brows.png';bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath='/Users/kosesena/Desktop/paypal-ai-hackathon/docs/gorseller/counterfoil-magaza.blend')

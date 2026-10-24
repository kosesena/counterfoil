"""Tailored hems and articulated-looking stylized human hands; preserves contact tracks."""
import bpy,math
from mathutils import Vector,Matrix
s=bpy.data.scenes['Counterfoil_Market_Composite']
if s.get('homi_hands_clothing'):raise RuntimeError('Already applied')
for role,cx in [('Customer',-3.6),('Store_Manager',-1.2)]:
 o=bpy.data.objects[role+'_Torso'];o.data=o.data.copy();basis=o.matrix_basis.copy();inv=basis.inverted()
 for v in o.data.vertices:
  p=basis@v.co
  if p.z<1.2:p.z=1.17;p.x=cx+(p.x-cx)*.96
  v.co=inv@p
 for mod in o.modifiers:
  if mod.type=='BEVEL':mod.width=.055;mod.segments=6
 for side in ['1','-1']:
  o=bpy.data.objects[role+'_Leg'+side];o.data=o.data.copy();basis=o.matrix_basis.copy();inv=basis.inverted()
  for v in o.data.vertices:
   p=basis@v.co
   if p.z>1:p.x=cx+(p.x-cx)*.86
   v.co=inv@p
# Local hand: broad palm, four separately bent fingers, opposing thumb.
verts=[];faces=[]
def ellipsoid(center,radii,quat=None):
 start=len(verts);nu=20;nv=12;c=Vector(center)
 for j in range(nv+1):
  a=math.pi*j/nv
  for i in range(nu):
   b=2*math.pi*i/nu;p=Vector((radii[0]*math.sin(a)*math.cos(b),radii[1]*math.sin(a)*math.sin(b),radii[2]*math.cos(a)))
   verts.append(tuple(c+(quat@p if quat else p)))
 for j in range(nv):
  for i in range(nu):
   k=start+j*nu+i;n=start+j*nu+(i+1)%nu;faces.append((k,n,n+nu,k+nu))
def segment(a,b,r):
 a,b=Vector(a),Vector(b);v=b-a;ellipsoid((a+b)/2,(r,r,v.length/2+r*.7),v.to_track_quat('Z','Y'))
ellipsoid((0,0,.17),(.65,.30,.64))
for x,length in [(-.47,.80),(-.16,.94),(.16,.90),(.46,.69)]:
 a=(x,0,-.24);b=(x,-.07,-.24-length*.62);c=(x,-.38,-.24-length*.82)
 segment(a,b,.14);segment(b,c,.125)
segment((-.54,-.06,.30),(-.82,-.31,-.04),.19);segment((-.82,-.31,-.04),(-.59,-.54,-.30),.155)
mesh=bpy.data.meshes.new('HOMI_HumanHand');mesh.from_pydata(verts,[],faces);mesh.update()
for p in mesh.polygons:p.use_smooth=True
for o in list(bpy.data.objects):
 original=o.name in [role+'_Hand'+side for role in ['Customer','Store_Manager'] for side in ['1','-1']]
 procedural=o.name.startswith(('PC_Customer','PC_Store_Manager')) and o.name.endswith('palm')
 if original or procedural:
  mat=o.data.materials[0];o.data=mesh.copy();o.data.materials.append(mat)
  if original:o.data.transform(Matrix.Diagonal((.58,.58,.58,1)))
  # Round knuckles smoothly; individual finger contours remain visible.
 if o.name.startswith(('PC_Customer','PC_Store_Manager')) and o.name.endswith('thumb'):
  o.data=bpy.data.meshes.new(o.name+'_Superseded')
s['homi_hands_clothing']='Four bent fingers and opposing thumb; cleaner shirt hem, tapered waistband. Contact animation preserved.'
r=bpy.data.scenes['HOMI_P6_Scan_Review'];bpy.context.window.scene=r;r.frame_set(646);r.camera=bpy.data.objects['PC_ScanCamera'];r.render.filepath='/Users/kosesena/Documents/Codex/2026-10-23/se/outputs/homi-hands-clothing.png';bpy.ops.render.render(write_still=True)
# Hands follow the forearm direction, with fingers pointing toward the held prop.
for role,sides,review in [('Customer',['R','L'],'HOMI_P6_Scan_Review'),('Store_Manager',['L'],'HOMI_P6_Manager_Review')]:
 sc=bpy.data.scenes[review];bpy.context.window.scene=sc
 for f in range(620,1141):
  sc.frame_set(f)
  for side in sides:
   palm=bpy.data.objects['PC_'+role+side+'palm'];elbow=bpy.data.objects['PC_'+role+side+'elbow']
   palm.rotation_mode='QUATERNION';palm.rotation_quaternion=(elbow.location-palm.location).to_track_quat('Z','Y');palm.keyframe_insert('rotation_quaternion',frame=f)
for role in ['Customer','Store_Manager']:
 o=bpy.data.objects[role+'_Torso']
 for m in o.modifiers:
  if m.type=='BEVEL':m.width=.095;m.segments=8
bpy.context.window.scene=r;r.frame_set(646);bpy.ops.render.render(write_still=True)
# Match palm width to sleeve cuff, keeping fingers visibly distinct.
for o in bpy.data.objects:
 if o.name.startswith(('PC_Customer','PC_Store_Manager')) and o.name.endswith('palm'):
  o.data.transform(Matrix.Diagonal((1.20,1.20,1.12,1)))
r.frame_set(646);bpy.ops.render.render(write_still=True)

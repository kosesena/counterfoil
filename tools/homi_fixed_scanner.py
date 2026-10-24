"""Sena: round hands, fixed scanner, one-handed cup returns. No save or commit."""
import bpy, math
from mathutils import Vector,Matrix,Quaternion
s=bpy.data.scenes['Counterfoil_Market_Composite'];r=bpy.data.scenes['HOMI_P6_Scan_Review'];bpy.context.window.scene=r
if s.get('homi_fixed_scanner'):raise RuntimeError('Already applied')
base=open('/Users/kosesena/Desktop/paypal-ai-hackathon/tools/homi_p6_choreography.py').read();c=bpy.data.collections['HOMI_P6_Choreography'];exec(base[base.index('WHITE='):base.index('# Internal-demo EAN')]);exec(base[base.index('def inst_matrix'):base.index('# Handheld reader assembly')])
bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20);temp=bpy.context.object;template=temp.data.copy();bpy.data.objects.remove(temp,do_unlink=True)
for o in list(bpy.data.objects):
 original=o.name in [role+'_Hand'+side for role in ['Customer','Store_Manager'] for side in ['1','-1']]
 procedural=o.name.startswith(('PC_Customer','PC_Store_Manager')) and o.name.endswith('palm')
 if original or procedural:
  mat=o.data.materials[0];o.data=template.copy();o.data.materials.append(mat)
  for p in o.data.polygons:p.use_smooth=True
 if o.name=='PC_ManagerIndex':o.data=bpy.data.meshes.new('PC_RoundHands_NoIndex')
scan=bpy.data.objects['PC_Handheld'];scan.animation_data_clear();scan.location=scan['rest_location'];scan.rotation_mode='QUATERNION';scan.rotation_quaternion=Quaternion()
roots=[bpy.data.objects['PC_Cup_%02d'%i] for i in range(1,5)]
starts=[Vector((x,y,.998)) for x,y in [(-13.50,-10.02),(-13.25,-10.02),(-13.50,-9.78),(-13.25,-9.78)]]
ends=[Vector((x,y,1.008)) for x,y in [(-13.48,-9.16),(-13.23,-9.16),(-13.48,-8.91),(-13.23,-8.91)]]
held=Vector((-13.39,-9.772,1.15));q=Quaternion((0,0,1),-math.pi/2);offset=Vector((.12,0,.095))
parts={side:{k:bpy.data.objects['PC_Customer'+side+k] for k in ['upper','fore','elbow','palm','thumb']} for side in ['R','L']}
palm=parts['R']['palm'];left=parts['L']['palm']
r.frame_set(619);initial={side:parts[side]['palm'].location.copy() for side in ['R','L']}
for root in roots:
 root.animation_data_clear();root.parent=palm;root.matrix_parent_inverse=Matrix.Diagonal(tuple(1/v for v in palm.scale)+(1,));root.rotation_mode='QUATERNION'
beam=bpy.data.objects['PC_ScanBeam'];beam.animation_data_clear()
def ease(t):t=max(0,min(1,t));return t*t*(3-2*t)
def cup_pos(i,f):
 dt=f-(632+i*36)
 if dt<0:return starts[i]
 if dt<10:return starts[i].lerp(held,ease(dt/10))
 if dt<18:return held
 if dt<30:return held.lerp(ends[i],ease((dt-18)/12))
 return ends[i]
for f in range(620,1141):
 r.frame_set(f)
 shoulders={side:shoulder('Customer',side)+inst_matrix('Customer').to_3x3()@Vector((-.055 if side=='R' else .055,0,.30)) for side in ['R','L']}
 rest={side:shoulders[side]+Vector((0,0,-.75)) for side in ['R','L']}
 idx=min(3,max(0,(f-632)//36));dt=f-(632+idx*36)
 if f<632:right=initial['R'].lerp(starts[0]+offset,ease((f-620)/12))
 elif f>=770:right=(ends[3]+offset).lerp(rest['R'],ease((f-770)/18))
 elif dt>=30 and idx<3:right=(ends[idx]+offset).lerp(starts[idx+1]+offset,ease((dt-30)/6))
 else:right=cup_pos(idx,f)+offset
 leftpos=initial['L'].lerp(rest['L'],ease((f-620)/10)) if f<630 else rest['L']
 for side,pos in [('R',right),('L',leftpos)]:
  set_arm(parts[side],shoulders[side],pos,f,side)
  h=parts[side]['palm'];h.rotation_mode='QUATERNION';h.rotation_quaternion=Quaternion();h.keyframe_insert('rotation_quaternion',frame=f)
 for i,root in enumerate(roots):
  # Real parent link; while carried, this local translation is constant.
  root.location=cup_pos(i,f)-right;root.rotation_quaternion=q
  root.keyframe_insert('location',frame=f);root.keyframe_insert('rotation_quaternion',frame=f)
 on=any(k<=f<=k+2 for k in [646,682,718,754]);beam.hide_render=not on;beam.hide_viewport=not on
 beam.keyframe_insert('hide_render',frame=f);beam.keyframe_insert('hide_viewport',frame=f)
 if on:
  a=Vector((-13.588,-9.772,1.24));b=held+q@Vector((0,-.077,.09));v=b-a
  beam.location=(a+b)/2;beam.rotation_mode='QUATERNION';beam.rotation_quaternion=v.to_track_quat('Z','Y');beam.scale=(1.2,1.2,v.length/.002)
  for path in ['location','rotation_quaternion','scale']:beam.keyframe_insert(path,frame=f)
# Designated shallow tray for scanned returns, away from incoming cups.
station=bpy.data.collections['HOMI_Return_Station'];mat=bpy.data.materials['HR_White']
tray=box('ScannedReturnTray',(-13.355,-9.035,.987),(.55,.52,.025),mat,station)
for name,loc,size in [('Back',(-13.62,-9.035,1.018),(.02,.52,.06)),('Front',(-13.09,-9.035,1.018),(.02,.52,.06)),('SideA',(-13.355,-9.285,1.018),(.55,.02,.06)),('SideB',(-13.355,-8.785,1.018),(.55,.02,.06))]:box('ReturnBin'+name,loc,size,mat,station)
for o in roots+[beam]+list(parts['R'].values())+list(parts['L'].values()):linear(o)
s['homi_fixed_scanner']='Round skin-tone hands. Handheld docked. Fixed vertical scanner reads four hand-parented cups; scanned cups deposited in separate tray. Counts/timing unchanged.'
r.frame_set(646);r.camera=bpy.data.objects['PC_ScanCamera'];r.render.filepath='/Users/kosesena/Documents/Codex/2026-10-23/se/outputs/homi-fixed-scanner.png';bpy.ops.render.render(write_still=True)

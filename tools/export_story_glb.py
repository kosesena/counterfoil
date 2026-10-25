"""Export HOMI's five-stop story as a compact, scrub-able animated GLB.
Run: Blender -b docs/gorseller/counterfoil-magaza.blend --python tools/export_story_glb.py
Full store, facade, street and cars share the same scene as the return story.
Rigid cast/collection transforms are baked; visibility uses glTF STEP scale tracks.
No autoplay, network calls or git operations. Source cameras/materials are saved.
"""
import bpy, math, json, struct, os, time
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/gorseller/homi-story.glb'
RENDERS=ROOT/'docs/gorseller/homi-story-previews';RENDERS.mkdir(exist_ok=True)
src=bpy.data.scenes['Counterfoil_Market_Composite'];FPS=24;START=1
# Shopping, the till and the e-mail are inserted by tools/homi_story_polish.py; at(f) maps an original frame
# to the extended story, so the step table and the events below are the original frames through at().
import sys;sys.path.insert(0,str(ROOT/'tools'));import homi_story_polish as POL;POL.polish();at=POL.at
END=POL.END
steps=[(1,1,at(619),170,'Entry, shopping, PayPal at till 01, the walk to returns'),(2,at(620),at(779),at(646),'Scan four cups; approved return100'),(3,at(780)-POL.MAIL_LEN,at(819),at(800),'Kiosk note with the injection; agent requests60; review required'),(4,at(820),at(949),at(830),'Reject60; approve new40; gateway recheck'),(5,at(950),at(1140),at(1055),'Provider confirms40; receipt')]
def log(*args):print('[HOMI STORY]',*args,flush=True)
def fcurves(o):
 a=o.animation_data.action if o.animation_data else None
 if a:
  for l in a.layers:
   for st in l.strips:
    for bag in st.channelbags:yield from bag.fcurves

def visibility_animated(o):return any(fc.data_path in ('hide_render','hide_viewport') for fc in fcurves(o))
def animated(o):
 p=o
 while p:
  if p.animation_data and p.animation_data.action:return True
  p=p.parent
 return False
# Minimized evaluation scene: do not evaluate restaurant, facade or street per frame.
for old in list(bpy.data.scenes):
 if old.name.startswith(('__HOMI_STORY_EVAL','HOMI_WEB_STORY')):bpy.data.scenes.remove(old)
evalscene=bpy.data.scenes.new('__HOMI_STORY_EVAL');bpy.context.window.scene=evalscene
names=['HOMI_Return_Station','HOMI_Return_Finish','HOMI_P6_Choreography','HOMI_Manager_Office','HOMI_Payment_01','HOMI_Payment_03']
selected={}
for name in names:
 col=bpy.data.collections[name];evalscene.collection.children.link(col)
 for o in col.all_objects:selected[o.name]=(o,None)
for name in ['Inst_Customer','Inst_Cart','Inst_Store_Manager']:
 inst=bpy.data.objects[name];evalscene.collection.objects.link(inst)
 for o in inst.instance_collection.all_objects:selected[name+'::'+o.name]=(o,inst)
for o in src.objects:
 if o.name.startswith(('SE_GateEntry','SE_GateExit','SE_BStand_')):
  if o.name not in evalscene.objects:evalscene.collection.objects.link(o)
  selected[o.name]=(o,None)
for old in list(bpy.data.collections):
 if old.name.startswith('__HOMI_EXPORT_CONTEXT'):bpy.data.collections.remove(old)
# Align exit gate panels around the mat center, matching the web player's fix.
for i,dx in enumerate([.39,.99,.49]):
 for obj in src.objects:
  if obj.name.startswith('SE_GateExit'+str(i)) and not obj.get('homi_gate_aligned'):
   obj.location.x+=dx;obj['homi_gate_aligned']=True
# Number the lanes in the order a customer walking in from the entrance reaches them (Sena, 25 Oct): returns is last.
for name,label in [('HP01_LaneNumber','01'),('HP03_LaneNumber','02'),('HR_LaneNumber','03')]:
 obj=bpy.data.objects.get(name)
 if obj and obj.type=='FONT':obj.data.body=label
# Static store context is evaluated once, then detached while sampling the cast.
environment=bpy.data.collections.new('__HOMI_EXPORT_CONTEXT');evalscene.collection.children.link(environment)
context_sources=['Cephe (gizle-göster)','Çatı','Kat 3 · Restoran','Kat 2 · Showroom','Kat 1 · Market','Bina (duvar+kolon)','Sokak']
for name in context_sources:
 for o in bpy.data.collections[name].all_objects:
  if o.hide_render or o.hide_viewport:continue
  if o.name in selected or o.name in ['Inst_Customer','Inst_Cart','Inst_Store_Manager']:continue
  if o.type not in ('MESH','CURVE','FONT','EMPTY'):continue
  if o.name not in evalscene.objects:environment.objects.link(o)
  if o.instance_type=='COLLECTION' and o.instance_collection:
   for part in o.instance_collection.all_objects:selected[o.name+'::'+part.name]=(part,o)
  elif o.type!='EMPTY':selected[o.name]=(o,None)
# Dedicated material IDs for live web overlays. Text stays separate editable geometry.
for objname,matname in [('HR_ScreenGlass','HOMI_SCREEN_MAT'),('Store_Manager_HandTabletScreen','HOMI_TABLET_MAT')]:
 o=bpy.data.objects[objname];mat=bpy.data.materials.get(matname)
 if not mat:mat=o.data.materials[0].copy();mat.name=matname
 o.data.materials[0]=mat
# The cart is parked and taken back for the checkout by tools/homi_story_polish.py.
# Exact camera names in original Blender scene as well as exported GLB.
def camera(name,loc,target,scale=None):
 o=bpy.data.objects.get(name)
 if not o:o=bpy.data.objects.new(name,bpy.data.cameras.new(name));src.collection.objects.link(o)
 if o.name not in evalscene.objects:evalscene.collection.objects.link(o)
 o.location=loc;o.rotation_mode='XYZ';o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 o.data.type='ORTHO' if scale else 'PERSP'
 if scale:o.data.ortho_scale=scale
 o.data.lens=45;o.data.clip_start=.02;o.data.clip_end=150
 return o
overview=camera('HOMI_OVERVIEW',(58,-78,48),(0,-5,7),108)
overview['purpose']='Initial full-store overview; transition to HOMI_STEP_1 on user input'
cams=[]
cams.append(camera('HOMI_STEP_1',(11.6,-7.5,2),(11.6,-12,1.2),7))
cams.append(camera('HOMI_STEP_2',(-11.6,-11.8,3.7),(-13.35,-9.75,1.3),3.1))
evalscene.frame_set(at(800));bpy.context.view_layer.update()
screen=bpy.data.objects['HR_ScreenGlass'].matrix_world.translation.copy()
cams.append(camera('HOMI_STEP_3',screen+Vector((2.5,0,.12)),screen,1.5))
evalscene.frame_set(at(830));bpy.context.view_layer.update()
inst=bpy.data.objects['Inst_Store_Manager'];tablet=bpy.data.objects['Store_Manager_HandTabletScreen']
M=inst.matrix_world@Matrix.Translation(-inst.instance_collection.instance_offset)@tablet.matrix_world
center=M.translation;normal=M.to_3x3()@Vector((0,0,1));normal.normalize()
o=camera('HOMI_STEP_4',center+normal*.8,center,.65)
o.rotation_mode='QUATERNION';o.rotation_quaternion=M.to_quaternion();cams.append(o)
cams.append(camera('HOMI_STEP_5',(-11.1,-7.7,1.8),(-13.12,-7.7,.87),2.1))
bpy.context.view_layer.update()
for cam,(i,a,b,preview,label) in zip(cams,steps):
 cam['frame_start']=a;cam['frame_end']=b;cam['preview_frame']=preview;cam['step_label']=label
# Saving source before flattening keeps main scene editable and leaves export-only data out.
bpy.context.window.scene=src;src.camera=overview
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'docs/gorseller/counterfoil-magaza.blend'))
bpy.context.window.scene=evalscene;evalscene.frame_set(1)
items=[]
for key,(o,inst) in selected.items():
 if o.type not in ('MESH','CURVE','FONT'):continue
 if any(k in o.name for k in ['Plinth','_Label']) and o.name.startswith(('Customer_','Store_Manager_')):continue
 if (o.hide_render or o.hide_viewport) and not visibility_animated(o):continue
 items.append({'key':key,'o':o,'inst':inst,'moving':animated(o) or bool(inst and animated(inst)),'visanim':visibility_animated(o)})
log('source objects',len(items))
# Temporarily expose geometry for evaluation; frame_set restores visibility animation.
visibility={it['o'].name:(it['o'].hide_render,it['o'].hide_viewport) for it in items}
for it in items:it['o'].hide_render=False;it['o'].hide_viewport=False
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
stage=bpy.data.scenes.new('HOMI_WEB_STORY');stage.render.fps=FPS;stage.frame_start=START;stage.frame_end=END
for it in items:
 o=it['o'];ev=o.evaluated_get(dg)
 try:me=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=False,depsgraph=dg)
 except Exception as e:log('mesh skipped',o.name,str(e));continue
 if not me.polygons:continue
 flat=bpy.data.objects.new('WEB_'+it['key'].replace('::','_'),me);stage.collection.objects.link(flat)
 flat['source_name']=o.name;flat['story_key']=it['key']
 if o.type=='FONT':flat['text']=o.data.body
 it['flat']=flat;it['t']=[];it['r']=[];it['s']=[];it['v']=[]
items=[it for it in items if 'flat' in it]
for name,(hr,hv) in visibility.items():bpy.data.objects[name].hide_render=hr;bpy.data.objects[name].hide_viewport=hv
# Include every visibility boundary, plus 12fps transform sampling for smooth interpolation.
frames=set(range(1,END+1,2))|{END}
for it in items:
 for fc in fcurves(it['o']):
  if fc.data_path.startswith('hide_'):
   for kp in fc.keyframe_points:
    f=int(round(kp.co.x));frames.update(k for k in [f-1,f,f+1] if START<=k<=END)
for _,a,b,p,_ in steps:frames.update([a,b,p])
evalscene.collection.children.unlink(environment)
frames=sorted(frames);C=Matrix.Rotation(-math.pi/2,4,'X');Ci=C.inverted()
for index,f in enumerate(frames):
 evalscene.frame_set(f);bpy.context.view_layer.update()
 for it in items:
  if index and not (it['moving'] or it['visanim']):continue
  o,inst=it['o'],it['inst'];M=o.matrix_world.copy()
  if inst:M=inst.matrix_world@Matrix.Translation(-inst.instance_collection.instance_offset)@M
  G=C@M@Ci;t,q,scale=G.decompose()
  qv=[q.x,q.y,q.z,q.w]
  if it['r'] and sum(a*b for a,b in zip(qv,it['r'][-1]))<0:qv=[-x for x in qv]
  it['t'].append(list(t));it['r'].append(qv);it['s'].append(list(scale));it['v'].append(not(o.hide_render or o.hide_viewport))
  if index==0:it['flat'].matrix_world=M
 if index%100==0:log('sample',index+1,'/',len(frames),'frame',f)
for cam in [overview]+cams+[bpy.data.objects['HOMI_STEP_PAY'],bpy.data.objects['HOMI_STEP_MAIL']]:stage.collection.objects.link(cam)
bpy.context.window.scene=stage
log('exporting static Draco geometry')
bpy.ops.export_scene.gltf(filepath=str(OUT),export_format='GLB',use_active_scene=True,export_apply=True,export_animations=False,export_cameras=True,export_lights=False,export_yup=True,export_extras=True,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=7)
# Append standard glTF animation channels. This avoids Blender's unsupported
# hide_render export and keeps all mesh transforms in one explicitly seekable clip.
raw=OUT.read_bytes();jsonlen=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+jsonlen]);offset=20+jsonlen;binlen=struct.unpack_from('<I',raw,offset)[0];blob=bytearray(raw[offset+8:offset+8+binlen]);doc.setdefault('bufferViews',[]);doc.setdefault('accessors',[])
def accessor(values,kind):
 while len(blob)%4:blob.append(0)
 start=len(blob);flat=[v for row in values for v in (row if isinstance(row,(tuple,list)) else [row])];blob.extend(struct.pack('<'+'f'*len(flat),*flat));vi=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(blob)-start})
 a={'bufferView':vi,'componentType':5126,'count':len(values),'type':kind}
 if kind=='SCALAR':a['min']=[min(values)];a['max']=[max(values)]
 ai=len(doc['accessors']);doc['accessors'].append(a);return ai
def reduce_keys(values,quat=False,tol=2e-5):
 stack=[]
 for i in range(len(values)):
  stack.append(i)
  while len(stack)>2:
   a,b,c=stack[-3:];t=(frames[b]-frames[a])/(frames[c]-frames[a]);v=[x+(y-x)*t for x,y in zip(values[a],values[c])]
   if quat:
    mag=math.sqrt(sum(x*x for x in v));v=[x/mag for x in v]
   if max(abs(x-y) for x,y in zip(v,values[b]))>tol:break
   stack.pop(-2)
 return stack
anim={'name':'HOMI_STORY','samplers':[],'channels':[],'extras':{'fps':FPS,'sourceStartFrame':1,'autoplay':False}}
nodebykey={n.get('extras',{}).get('story_key'):i for i,n in enumerate(doc['nodes'])}
def channel(node,path,values,kind,indices,interp='LINEAR'):
 times=[max(0,(frames[i]-1)/FPS-(1e-5 if interp=='STEP' else 0)) for i in indices];inp=accessor(times,'SCALAR');out=accessor([values[i] for i in indices],kind);si=len(anim['samplers']);anim['samplers'].append({'input':inp,'output':out,'interpolation':interp});anim['channels'].append({'sampler':si,'target':{'node':node,'path':path}})
rootnodes=doc['scenes'][doc.get('scene',0)]['nodes'];dynamic=0
for it in items:
 ni=nodebykey[it['key']];node=doc['nodes'][ni];node.pop('matrix',None)
 for key,path,kind in [('t','translation','VEC3'),('r','rotation','VEC4'),('s','scale','VEC3')]:
  values=it[key];node[path]=values[0]
  if any(max(abs(a-b) for a,b in zip(v,values[0]))>1e-6 for v in values[1:]):
   channel(ni,path,values,kind,reduce_keys(values,key=='r'));dynamic+=1
 vis=it['v']
 if not all(vis):
  parent=len(doc['nodes']);doc['nodes'].append({'name':'VIS_'+it['o'].name,'children':[ni],'scale':[1,1,1] if vis[0] else [0,0,0],'extras':{'visibilityFor':it['o'].name}})
  if ni in rootnodes:rootnodes[rootnodes.index(ni)]=parent
  else:
   for n in doc['nodes'][:-1]:
    if ni in n.get('children',[]):n['children'][n['children'].index(ni)]=parent;break
  indices=[0]+[i for i in range(1,len(vis)) if vis[i]!=vis[i-1]]
  if len(indices)>1:channel(parent,'scale',[[1,1,1] if v else [0,0,0] for v in vis],'VEC3',indices,'STEP')
for node in doc['nodes']:
 if node.get('extras',{}).get('story_key','').startswith(('SE_','Inst_Shelf','Inst_L2','Inst_CartCorral')):node.pop('extras',None)
doc['animations']=[anim];doc['buffers'][0]['byteLength']=len(blob)
doc['asset']['extras']={'fps':FPS,'frameToSeconds':'(frame - 1) / 24','autoplay':False,'initialCamera':'HOMI_OVERVIEW','steps':[{'camera':'HOMI_STEP_'+str(i),'frames':[a,b],'seconds':[(a-1)/FPS,(b-1)/FPS],'previewFrame':p,'label':label} for i,a,b,p,label in steps]}
while len(blob)%4:blob.append(0)
j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4);length=12+8+len(j)+8+len(blob)
OUT.write_bytes(struct.pack('<4sII',b'glTF',2,length)+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(blob),b'BIN\0')+blob)
manifest={'file':str(OUT.relative_to(ROOT)),'bytes':OUT.stat().st_size,'megabytes':OUT.stat().st_size/1e6,'fps':FPS,'frameToSeconds':'(frame - 1) / 24','animation':'HOMI_STORY','autoplay':False,'initialCamera':'HOMI_OVERVIEW','overviewFrame':170,'cameraStops':doc['asset']['extras']['steps'],'materials':['HOMI_SCREEN_MAT','HOMI_TABLET_MAT'],'nodes':len(doc['nodes']),'channels':len(anim['channels']),'sampledFrames':len(frames),'notes':['Use an AnimationMixer, pause it and setTime after each user button; the GLB does not autoplay.','Visibility parent scale tracks use STEP. Do not discard these tracks.','Screen lettering is separate mesh nodes, with source_name and text extras. Hide/replace these when rendering live data.','Mesh geometry is Draco compressed; animation accessors are standard float32.']}
manifest['environment']={'scope':'Full store, facade, street, cars and all storeys','initialCamera':'HOMI_OVERVIEW','laneLabelsFromEntrance':['01 CHECKOUT','02 CHECKOUT','03 RETURNS'],'exitGatePanelX':[-14.06,-12.56,-11.06],'originalSizeTargetMB':15,'sizeTargetExceeded':OUT.stat().st_size>=15_000_000}
manifest['events']={'scanCounts':{'1/4':at(646),'2/4':at(682),'3/4':at(718),'4/4':at(754)},'returnApproved100':at(768),'reviewRequired':at(780),'reject60':at(820),'fresh40Ready':at(848),'approve40AndRecheck':at(860),'providerPending':at(950),'providerConfirmed':at(1020),'receiptFullyOut':at(1055)}
manifest['story']={'tillArrive':POL.TILL_STOP,'paid':POL.PAY_SENT,'tillLeave':POL.TILL_LEAVE,'atReturns':POL.LAST,'mailStart':POL.MAIL_START,'mailSent':POL.MAIL_SENT,'payCamera':'HOMI_STEP_PAY','mailCamera':'HOMI_STEP_MAIL','followFrom':172,'shifts':[[o,n] for o,n,_ in POL.SHIFTS]}
manifest['notes'].extend(['Step 2 prioritizes hand/cup/scanner; show scan count in the web overlay, as the customer partially occludes the physical screen.','Step 1 is an entrance camera stop; seek previewFrame170 for the button snapshot. A static camera does not follow the entire walk to the checkout.'])
(ROOT/'docs/gorseller/homi-story.json').write_text(json.dumps(manifest,indent=2))
log('DONE',OUT.stat().st_size,'bytes',len(anim['channels']),'channels')
if OUT.stat().st_size>=15_000_000:log('Full environment exceeds original15MB target; see manifest size')
# Render five representative source frames without changing main file's saved state.
evalscene.world=bpy.data.scenes['HOMI_P6_Scan_Review'].world;evalscene.render.engine=src.render.engine
for n in ['PC_Key','PC_Fill','PC_ManagerKey']:
 if n in bpy.data.objects and n not in evalscene.objects:evalscene.collection.objects.link(bpy.data.objects[n])
sun=bpy.data.objects.new('StoryPreviewSun',bpy.data.lights.new('StoryPreviewSun','SUN'));evalscene.collection.objects.link(sun);sun.data.energy=1.5;sun.rotation_euler=(.4,-.5,-.4)
light=bpy.data.objects.new('StoryPreviewEntryLight',bpy.data.lights.new('StoryPreviewEntryLight','AREA'));evalscene.collection.objects.link(light);light.location=(11,-12,10);light.data.energy=1800;light.data.shape='DISK';light.data.size=10
evalscene.collection.children.link(environment)
for name in ['Composite_Layout']:
 for obj in bpy.data.collections[name].all_objects:
  if obj.type=='LIGHT' and obj.name not in evalscene.objects:evalscene.collection.objects.link(obj)
evalscene.render.resolution_x=1280;evalscene.render.resolution_y=720;evalscene.render.resolution_percentage=100
bpy.context.window.scene=evalscene
evalscene.frame_set(170);evalscene.camera=overview;evalscene.render.filepath=str(RENDERS/'overview.png');bpy.ops.render.render(write_still=True)
for cam,(i,a,b,preview,label) in zip(cams,steps):
 if os.environ.get('HOMI_RENDER_STEPS') and str(i) not in os.environ['HOMI_RENDER_STEPS'].split(','):continue
 evalscene.frame_set(preview);evalscene.camera=cam;evalscene.render.filepath=str(RENDERS/('step-%d.png'%i));bpy.ops.render.render(write_still=True);log('render step',i)

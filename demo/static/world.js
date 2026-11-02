import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
const stage=document.getElementById('worldStage');
const status=document.getElementById('worldStatus');
const start=document.getElementById('worldLoad');
const result=document.getElementById('worldResult');
let renderer,controls,camera,scene,resize,home,loading=false,loadPromise=null;
const fromBlender=(p)=>new THREE.Vector3(p[0],p[2],-p[1]);
function draw(){if(!renderer)return;renderer.render(scene,camera);placeBadges();}
async function load(){
 if(renderer)return;
 if(loading)return loadPromise;
 loading=true;start.disabled=true;status.textContent='Opening the 3D store…';
 loadPromise=(async()=>{try {
  const meta=await fetch('/static/world/camera.json').then(r=>{if(!r.ok)throw Error();return r.json();});
  const draco=new DRACOLoader().setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/libs/draco/gltf/');
  const model=await new GLTFLoader().setDRACOLoader(draco).loadAsync('/static/world/homi-meshy.glb',e=>{if(e.total)status.textContent=`Opening the 3D store… ${Math.round(e.loaded/e.total*100)}%`;});
  draco.dispose();
  scene=new THREE.Scene();scene.background=new THREE.Color('#e9e3da');
  const r=new THREE.WebGLRenderer({antialias:true});renderer=r;
  r.setPixelRatio(Math.min(devicePixelRatio,1.5));r.toneMapping=THREE.ACESFilmicToneMapping;r.toneMappingExposure=.8;
  const pm=new THREE.PMREMGenerator(r);scene.environment=pm.fromScene(new RoomEnvironment(),.04).texture;pm.dispose();
  scene.add(new THREE.HemisphereLight(0xfff7ee,0xd9cfc2,.45));
  const sun=new THREE.DirectionalLight(0xffffff,.9);sun.position.set(-6,12,14);scene.add(sun);
  scene.add(model.scene);
  buildActors(model.scene);
  camera=new THREE.OrthographicCamera(-5,5,5,-5,.05,300);
  home={position:fromBlender(meta.position),target:fromBlender(meta.target),scale:meta.scale};
  camera.position.copy(home.position);camera.lookAt(home.target);
  r.domElement.setAttribute('aria-label','Interactive HOMI store with Nella, Reader, Runner, Counterfoil, the store manager and PayPal. Drag to rotate; scroll to zoom.');
  stage.append(r.domElement);
  controls=new OrbitControls(camera,r.domElement);controls.target.copy(home.target);controls.minZoom=.6;controls.maxZoom=3;controls.maxPolarAngle=Math.PI*.48;controls.enablePan=false;controls.addEventListener('change',draw);controls.update();
  resize=()=>{const w=stage.clientWidth,h=stage.clientHeight;camera.left=-home.scale/2;camera.right=home.scale/2;camera.top=home.scale*h/w/2;camera.bottom=-home.scale*h/w/2;camera.updateProjectionMatrix();r.setSize(w,h);draw();};
  new ResizeObserver(resize).observe(stage);resize();
  stage.classList.add('is-ready');start.hidden=true;document.getElementById('worldReset').disabled=false;
  status.textContent='Drag to look around · scroll or pinch to zoom';
 }catch(e){renderer?.dispose();renderer=null;stage.querySelector('canvas')?.remove();status.textContent='3D could not load. The approved Blender preview is shown; you can still try the simulator below.';start.disabled=false;start.textContent='Retry 3D';}
 loading=false;})();
 return loadPromise;
}
start.addEventListener('click',load);
document.getElementById('worldReset').addEventListener('click',()=>{if(!controls)return;camera.position.copy(home.position);camera.zoom=1;controls.target.copy(home.target);controls.update();resize();});
if(matchMedia('(min-width: 761px)').matches){const io=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){io.disconnect();load();}},{rootMargin:'200px'});io.observe(stage);}

// ---- The crew as actors -------------------------------------------------------------------------------
// Each character is a group of meshes (glTF node names, '|' kept, spaces became '_'). A group is pivoted at
// the character's feet, so a hop or a head shake turns the whole figure in place. Counterfoil's felt parts
// arrive as 30 separate meshes; an older GLB where it was merged into the store still gets a badge anchor.
const ACTORS={nella:'Nella |',reader:'Reader |',runner:'Runner |',counterfoil:'FELT Guest |',manager:'Manager |',paypal:'PayPal |'};
const FALLBACK={counterfoil:[-12.05,-8.18,2.2]}; // Blender coordinates of the felt Counterfoil's head
const actors={};
function buildActors(root){
 const groups={};
 root.traverse(o=>{if(!o.isMesh)return;const n=o.name.replace(/_/g,' ');for(const[k,p]of Object.entries(ACTORS))if(n.startsWith(p)){(groups[k]||=[]).push(o);break;}});
 root.updateMatrixWorld(true);
 for(const[k,meshes]of Object.entries(groups)){
  const box=new THREE.Box3();meshes.forEach(m=>box.expandByObject(m));
  const pivot=new THREE.Group();pivot.position.set((box.min.x+box.max.x)/2,box.min.y,(box.min.z+box.max.z)/2);root.add(pivot);pivot.updateMatrixWorld(true);
  meshes.forEach(m=>pivot.attach(m));
  actors[k]={pivot,height:box.max.y-box.min.y,base:pivot.position.clone()};
 }
 for(const[k,p]of Object.entries(FALLBACK))if(!actors[k]){const v=fromBlender(p);actors[k]={pivot:null,anchor:v,height:0};}
}
function headOf(key){const a=actors[key];if(!a)return null;if(!a.pivot)return a.anchor.clone();return a.pivot.position.clone().add(new THREE.Vector3(0,a.height,0));}

// ---- Motion: short, one per click, nothing loops ------------------------------------------------------
const still=matchMedia('(prefers-reduced-motion: reduce)').matches;
let moves=[],ticking=false;
function animate(key,kind){
 const a=actors[key];if(!a?.pivot||still){draw();return;}
 moves=moves.filter(m=>m.key!==key);a.pivot.position.copy(a.base);a.pivot.rotation.set(0,0,0);
 moves.push({key,kind,t0:performance.now(),ms:kind==='shake'?900:kind==='nod'?800:700});
 if(!ticking){ticking=true;requestAnimationFrame(tick);}
}
function tick(now){
 moves=moves.filter(m=>{
  const a=actors[m.key],t=Math.min(1,(now-m.t0)/m.ms),e=Math.sin(Math.PI*t);
  if(m.kind==='hop'){a.pivot.position.y=a.base.y+Math.abs(Math.sin(2*Math.PI*t))*.22*(1-t*.4);}
  else if(m.kind==='shake'){a.pivot.rotation.y=Math.sin(6*Math.PI*t)*.32*(1-t);}
  else if(m.kind==='nod'){a.pivot.rotation.x=Math.sin(4*Math.PI*t)*.12*(1-t);}
  if(t>=1){a.pivot.position.copy(a.base);a.pivot.rotation.set(0,0,0);return false;}
  return true;
 });
 draw();
 if(moves.length)requestAnimationFrame(tick);else ticking=false;
}

// ---- Felt speech badges over the store -----------------------------------------------------------------
const layer=document.createElement('div');layer.className='world-badges';layer.setAttribute('aria-hidden','true');stage.append(layer);
let badges=[];
function showBadges(list){
 layer.replaceChildren();badges=list.map(b=>{const el=document.createElement('div');el.className='world-badge '+(b.tone||'');el.innerHTML=b.html;layer.append(el);return{el,key:b.key};});
 placeBadges();requestAnimationFrame(()=>badges.forEach(b=>b.el.classList.add('show')));
}
function placeBadges(){
 if(!renderer||!badges.length)return;
 const w=stage.clientWidth,h=stage.clientHeight;
 for(const b of badges){
  const p=headOf(b.key);if(!p){b.el.style.display='none';continue;}
  p.project(camera);
  const x=(p.x+1)/2*w,y=(1-p.y)/2*h,half=b.el.offsetWidth/2;
  b.el.style.left=Math.max(half+8,Math.min(w-half-8,x))+'px';b.el.style.top=Math.max(b.el.offsetHeight+26,y)+'px';
 }
}

// ---- From a recorded or live run to six steps ---------------------------------------------------------
const MONEY=new Set(['refund','charge','void']);
const esc=(s)=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const money=(s)=>s.args?.amount?`${s.args.amount} ${s.args.currency||''}`.trim():'';
const callText=(s)=>`<code>${esc(s.tool)}(${esc([s.args?.order_no,money(s)].filter(Boolean).join(', '))})</code>`;
const movedSteps=(row)=>(row?.steps||[]).filter(s=>MONEY.has(s.tool)&&(s.rail_state==='succeeded'||s.rail_state==='unknown'));
function stepsFor({scenario,kind,rows}){
 const cf=rows.counterfoil,none=rows.none,steps=[];
 const subject=scenario?.email?.subject||'Your own e-mail';
 const body=(scenario?.email?.body_text||'').replace(/\s+/g,' ').trim();
 const attack=kind==='attack';
 steps.push({key:'nella',label:attack?'Nella writes in':'A customer writes in',move:'hop',html:`<b>${attack?'Nella · a note with a hidden ask':'A customer writes in'}</b>“${esc(subject)}”${body?`<br><small>${esc(body.length>120?body.slice(0,118)+'…':body)}</small>`:''}`});
 const rd=cf?.reader;
 steps.push({key:'reader',label:'Reader reads the note',move:'hop',html:rd?`<b>Reader · hands off</b>${esc([rd.siparis_no,rd.istek,rd.tutar&&`${rd.tutar} ${rd.para_birimi||''}`].filter(Boolean).join(' · '))}${rd.not?`<br><small>note: “${esc(rd.not.slice(0,80))}”</small>`:''}`:'<b>Reader</b>Could not read the note.'});
 // Every call goes through the gate, reads included: a blocked lookup is often where an attack stops.
 const calls=cf?.steps||[];
 steps.push({key:'runner',label:'Runner asks Counterfoil',move:'hop',html:calls.length?`<b>Runner · asks</b>${calls.map(callText).join('<br>')}`:'<b>Runner</b>Made no call.'});
 const worst=calls.find(s=>s.decision==='BLOCK')||calls.find(s=>s.decision==='APPROVAL')||calls[0];
 if(!worst)steps.push({key:'counterfoil',label:'Counterfoil checks the record',move:'nod',html:'<b>Counterfoil</b>Nothing to check: no call reached the gate.'});
 // The scenario's expected reason, in words ("USD 60.00 reserved plus USD 60.00 attempted exceeds approved USD
 // 100.00"), only when this run's decision is the expected one; the replayed rows carry no reasons of their own.
 const dec=worst?.decision||'PASS',reason=scenario?.expected_reason||'';
 const why=dec===scenario?.expected_gateway_decision&&reason.includes(':')?reason.slice(reason.indexOf(':')+1).split(/;|\. |, so /)[0].trim():'';
 const verdict={BLOCK:'BLOCK · checked against the store record',APPROVAL:'HOLD · a person decides',PASS:'PASS · matches the store record'}[dec];
 const whichCall=calls.length>1&&dec!=='PASS'?`<br><small>on ${callText(worst)}</small>`:'';
 if(worst)steps.push({key:'counterfoil',label:'Counterfoil checks the record',move:dec==='BLOCK'?'shake':dec==='APPROVAL'?'nod':'hop',tone:dec,html:`<b>Counterfoil</b>${verdict}${whichCall}${dec!=='PASS'&&why?`<br><small>${esc(why)}</small>`:''}`});
 if(calls.some(s=>s.decision==='APPROVAL'))steps.push({key:'manager',label:'The manager reviews the held call',move:'hop',tone:'APPROVAL',html:'<b>Store manager</b>A held call is waiting: approve or reject it in step 3 below, after paying with PayPal.'});
 const moved=movedSteps(cf);
 steps.push({key:'paypal',label:'PayPal / Braintree',move:moved.length?'hop':'nod',tone:moved.length?'PASS':'',html:moved.length?`<b>PayPal · Braintree</b>Moved: ${moved.map(callText).join('<br>')}`:'<b>PayPal · Braintree</b>No money moved.'});
 const leaked=movedSteps(none);
 if(attack&&none)steps.push({key:'paypal',label:'And without Counterfoil?',move:leaked.length?'shake':'nod',tone:leaked.length?'harm':'',html:leaked.length?`<b>Without the gate</b>${leaked.map(callText).join('<br>')} would have left HOMI.`:'<b>Without the gate</b>This model was not fooled: nothing would have left either.'});
 return steps;
}

const bar=document.getElementById('worldSteps'),label=document.getElementById('worldStepLabel'),prev=document.getElementById('worldPrev'),next=document.getElementById('worldNext');
let play=null;
function show(i){
 if(!play)return;play.i=i;const s=play.steps[i];
 bar.hidden=false;label.textContent=`Step ${i+1} of ${play.steps.length} · ${s.label}`;
 document.getElementById('worldCaption').innerHTML=s.html;
 prev.disabled=i===0;next.disabled=i===play.steps.length-1;next.textContent=i===play.steps.length-2?'Last step ›':'Next step ›';
 showBadges([s]);animate(s.key,s.move);
}
async function watch(){
 if(!play)return;
 stage.scrollIntoView({behavior:still?'auto':'smooth',block:'center'});
 if(!renderer){await load();if(!renderer)return;}
 show(0);next.focus({preventScroll:true});
}
function stop(){play=null;bar.hidden=true;showBadges([]);}
prev.addEventListener('click',()=>play&&show(Math.max(0,play.i-1)));
next.addEventListener('click',()=>play&&show(Math.min(play.steps.length-1,play.i+1)));
document.getElementById('worldClose').addEventListener('click',stop);
window.addEventListener('homi:comparison',e=>{result.textContent=e.detail;});
window.addEventListener('homi:run',e=>{
 play={steps:stepsFor(e.detail),i:0};bar.hidden=true;showBadges([]);
 const b=document.createElement('button');b.textContent='Watch it in the store ↑';b.addEventListener('click',watch);
 result.append(b);
});
window.addEventListener('homi:clear',stop);

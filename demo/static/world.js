import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { VIEW, fitDistance, loadModel, makeView, dressStore, makeCast, startPeople } from '/static/world/store.js';
const stage=document.getElementById('worldStage');
const status=document.getElementById('worldStatus');
const start=document.getElementById('worldLoad');
const result=document.getElementById('worldResult');
let renderer,controls,camera,scene,resize,renderView,people=null,loading=false,loadPromise=null;
function draw(){if(!renderer)return;renderView();placeBadges();}
async function load(){
 if(renderer)return;
 if(loading)return loadPromise;
 loading=true;start.disabled=true;status.textContent='Opening the 3D store…';
 loadPromise=(async()=>{try {
  const model=await loadModel(p=>{status.textContent=`Opening the 3D store… ${p}%`;});
  const view=makeView(stage.clientWidth,stage.clientHeight);({scene,camera,renderer}=view);renderView=view.render;const r=renderer;
  dressStore(scene,model.scene);Object.assign(actors,makeCast(model.scene));
  camera.position.copy(VIEW.target).addScaledVector(VIEW.dir,fitDistance(stage.clientWidth/stage.clientHeight));camera.lookAt(VIEW.target);
  r.domElement.setAttribute('aria-label','Interactive HOMI store with Nella, Reader, Runner, Counterfoil, the store manager and the payment rail. Drag to rotate; scroll or pinch to zoom.');
  stage.append(r.domElement);
  controls=new OrbitControls(camera,r.domElement);controls.target.copy(VIEW.target);controls.minDistance=3;controls.maxDistance=60;controls.maxPolarAngle=Math.PI*.48;controls.enablePan=false;controls.addEventListener('change',draw);controls.update();
  resize=()=>{const w=stage.clientWidth,h=stage.clientHeight;if(!w||!h)return;view.setSize(w,h);const dir=camera.position.clone().sub(controls.target).normalize();camera.position.copy(controls.target).addScaledVector(dir,fitDistance(w/h));controls.update();draw();};
  new ResizeObserver(resize).observe(stage);resize();
  people=startPeople({scene,root:model.scene,renderer:r,actors,draw,calm:still,canvas:r.domElement});
  stage.classList.add('is-ready');start.hidden=true;document.getElementById('worldReset').disabled=false;
  status.textContent='Drag to look around · scroll or pinch to zoom';
 }catch(e){renderer?.dispose();renderer=null;stage.querySelector('canvas')?.remove();status.textContent='3D could not load. The approved Blender preview is shown; you can still try the simulator below.';start.disabled=false;start.textContent='Retry 3D';}
 loading=false;})();
 return loadPromise;
}
start.addEventListener('click',load);
document.getElementById('worldReset').addEventListener('click',()=>{if(!controls)return;controls.target.copy(VIEW.target);camera.position.copy(VIEW.target).addScaledVector(VIEW.dir,fitDistance(stage.clientWidth/stage.clientHeight));camera.zoom=1;controls.update();resize();});
if(matchMedia('(min-width: 761px)').matches){const io=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){io.disconnect();load();}},{rootMargin:'200px'});io.observe(stage);}

// ---- The cast as actors, made in store.js -------------------------------------------------------------
const actors={};
function headOf(key){const a=actors[key];if(!a)return null;if(!a.pivot)return a.anchor.clone();return a.pivot.position.clone().add(new THREE.Vector3(0,a.height,0));}

// ---- Motion: one gesture per click -------------------------------------------------------------------
const still=matchMedia('(prefers-reduced-motion: reduce)').matches;
function animate(key,kind){people?.gesture(key,{hop:'wave',shake:'shake',nod:'nod'}[kind]||kind);}

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

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
const stage=document.getElementById('worldStage');
const status=document.getElementById('worldStatus');
const start=document.getElementById('worldLoad');
let renderer,controls,camera,scene,resize,home,loading=false;
const fromBlender=(p)=>new THREE.Vector3(p[0],p[2],-p[1]);
function draw(){renderer?.render(scene,camera);}
async function load(){
 if(renderer||loading)return;
 loading=true;start.disabled=true;status.textContent='Opening the 3D store…';
 try {
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
  camera=new THREE.OrthographicCamera(-5,5,5,-5,.05,300);
  home={position:fromBlender(meta.position),target:fromBlender(meta.target),scale:meta.scale};
  camera.position.copy(home.position);camera.lookAt(home.target);
  r.domElement.setAttribute('aria-label','Interactive HOMI store with Nella, Counterfoil and PayPal. Drag to rotate; scroll to zoom.');
  stage.append(r.domElement);
  controls=new OrbitControls(camera,r.domElement);controls.target.copy(home.target);controls.minZoom=.6;controls.maxZoom=3;controls.maxPolarAngle=Math.PI*.48;controls.enablePan=false;controls.addEventListener('change',draw);controls.update();
  resize=()=>{const w=stage.clientWidth,h=stage.clientHeight;camera.left=-home.scale/2;camera.right=home.scale/2;camera.top=home.scale*h/w/2;camera.bottom=-home.scale*h/w/2;camera.updateProjectionMatrix();r.setSize(w,h);draw();};
  new ResizeObserver(resize).observe(stage);resize();
  stage.classList.add('is-ready');start.hidden=true;document.getElementById('worldReset').disabled=false;
  status.textContent='Drag to look around · scroll or pinch to zoom';
 }catch(e){renderer?.dispose();renderer=null;stage.querySelector('canvas')?.remove();status.textContent='3D could not load. The approved Blender preview is shown; you can still try the simulator below.';start.disabled=false;start.textContent='Retry 3D';}
 loading=false;
}
start.addEventListener('click',load);
document.getElementById('worldReset').addEventListener('click',()=>{if(!controls)return;camera.position.copy(home.position);camera.zoom=1;controls.target.copy(home.target);controls.update();resize();});
if(matchMedia('(min-width: 761px)').matches){const io=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){io.disconnect();load();}},{rootMargin:'200px'});io.observe(stage);}
window.addEventListener('homi:comparison',e=>{document.getElementById('worldResult').textContent=e.detail;});

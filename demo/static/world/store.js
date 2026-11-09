// The HOMI store, built in tools/build_homi_store.py: loads the model, lights it, and keeps its people moving.
// A person is a tree of joints (hip, knee, shoulder, elbow, spine, head) driven here, so a step can make someone walk,
// wave, nod or stamp. Nothing here advances the story; only the ambient life runs by itself.
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";

export const CAST = { nella: "Nella", reader: "Reader", runner: "Runner", counterfoil: "Counterfoil", manager: "Manager", paypal: "PayPal" };
const BASE_YAW = { nella: Math.PI / 2 };
export const VIEW = { target: new THREE.Vector3(0.1, 0.55, -0.1), dir: new THREE.Vector3(0.9, 8.1, 16.6).normalize(), width: 19.2, near: 7.2 };
const FOV = 30;
export const fitDistance = (aspect) => Math.max(VIEW.width / aspect, 8.6) / (2 * Math.tan((FOV / 2) * Math.PI / 180));

export async function loadModel(onProgress) {
  return new GLTFLoader().loadAsync("/static/world/homi-store.glb", (e) => { if (e.total) onProgress?.(Math.round((e.loaded / e.total) * 100)); });
}

export function makeView(canvasW, canvasH) {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0xc9bfb1);
  const camera = new THREE.PerspectiveCamera(FOV, canvasW / canvasH, 0.1, 200);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  const composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(4, 4, { samples: 4, type: THREE.HalfFloatType }));
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(4, 4), 0.3, 0.6, 0.88); composer.addPass(bloom); composer.addPass(new OutputPass());
  const setSize = (w, h) => { renderer.setSize(w, h); composer.setPixelRatio(renderer.getPixelRatio()); composer.setSize(w, h); camera.aspect = w / h; camera.updateProjectionMatrix(); };
  const overlay = new THREE.Scene(); // the story's tags: drawn after bloom so their text stays crisp
  const render = () => { composer.render(); renderer.autoClear = false; renderer.clearDepth(); renderer.toneMapping = THREE.NoToneMapping; renderer.render(overlay, camera); renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.autoClear = true; };
  return { scene, overlay, camera, renderer, composer, setSize, render };
}

export function dressStore(scene, root) {
  scene.add(new THREE.HemisphereLight(0xfff6ea, 0x8a7a6a, 1.2));
  const key = new THREE.DirectionalLight(0xfff0dc, 2.0); key.position.set(6, 12, 8); key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -0.0005; key.shadow.normalBias = 0.02;
  Object.assign(key.shadow.camera, { left: -11, right: 11, top: 8, bottom: -8, near: 1, far: 40 });
  scene.add(key);
  const lamps = [];
  root.traverse((o) => {
    if (o.name.startsWith("Lamp_")) lamps.push(o);
    if (o.isMesh) { const clear = o.material.transparent; o.castShadow = !clear && !/Floor|Platform|LED/i.test(o.material.name); o.receiveShadow = !clear; }
  });
  for (const o of lamps) { const l = new THREE.PointLight(0xffc27a, 1.7, 4.4, 2); o.getWorldPosition(l.position); scene.add(l); }
  scene.add(root);
}

export function makeCast(root) {
  const actors = {};
  for (const [k, name] of Object.entries(CAST)) {
    const pivot = root.getObjectByName(name); if (!pivot) continue;
    const box = new THREE.Box3().setFromObject(pivot);
    actors[k] = { pivot, name, height: box.max.y - box.min.y, base: pivot.position.clone(), ground: pivot.position.clone(), yaw: BASE_YAW[k] || 0, machine: k === "counterfoil" || k === "paypal" };
    pivot.rotation.y = actors[k].yaw;
  }
  return actors;
}

function joints(root, name) {
  const g = (n) => root.getObjectByName(`${name}_${n}`);
  return { legL: g("LegL"), legR: g("LegR"), kneeL: g("KneeL"), kneeR: g("KneeR"), armL: g("ArmL"), armR: g("ArmR"), elbowL: g("ElbowL"), elbowR: g("ElbowR"), spine: g("Spine"), head: g("Head") };
}

// A gesture is a function of its progress: it returns joint angles on top of the idle or walking pose.
const bump = (u, a = 0.18, b = 0.82) => Math.min(1, Math.min(u / a, (1 - u) / (1 - b)));
const GESTURES = {
  wave: { ms: 1700, f: (u, t) => { const e = bump(u); return { armR: [0, 0, 2.55 * e], elbowR: [-0.25 * e, 0, Math.sin(t * 13) * 0.42 * e], head: [0, 0, 0.1 * e] }; } },
  nod: { ms: 1100, f: (u) => ({ head: [Math.sin(u * Math.PI * 4) * 0.3 * (1 - u * 0.5), 0, 0] }) },
  shake: { ms: 1200, f: (u) => ({ head: [0, Math.sin(u * Math.PI * 6) * 0.45 * (1 - u * 0.5), 0] }) },
  read: { ms: 2500, f: (u, t) => { const e = bump(u, 0.12, 0.88); return { armL: [-1.0 * e, 0, -0.16 * e], armR: [-1.0 * e, 0, 0.16 * e], elbowL: [-1.1 * e, 0, 0], elbowR: [-1.1 * e, 0, 0], head: [0.34 * e, Math.sin(t * 2.6) * 0.16 * e, 0] }; } },
  handover: { ms: 1500, f: (u) => { const e = bump(u, 0.3, 0.75); return { armR: [-1.45 * e, 0, 0], elbowR: [-0.25 * e, 0, 0], spine: [0.1 * e, 0, 0] }; } },
  type: { ms: 2300, f: (u, t) => { const e = bump(u, 0.12, 0.88); return { armL: [-0.75 * e + Math.sin(t * 19) * 0.05 * e, 0, -0.1 * e], armR: [-0.75 * e + Math.cos(t * 23) * 0.05 * e, 0, 0.1 * e], elbowL: [-0.85 * e, 0, 0], elbowR: [-0.85 * e, 0, 0], head: [0.26 * e, 0, 0] }; } },
  press: { ms: 1300, f: (u) => { const e = bump(u, 0.3, 0.72); return { armR: [-1.15 * e, 0, 0], elbowR: [-0.4 * e, 0, 0], head: [0.2 * e, 0, 0], spine: [0.1 * e, 0, 0] }; } },
  approve: { ms: 1900, f: (u) => { const e = bump(u, 0.2, 0.8); return { armR: [-1.0 * e, 0, 0.18 * e], elbowR: [-1.75 * e, 0, 0], head: [Math.sin(u * Math.PI * 4) * 0.22 * e, 0, 0] }; } },
  shrug: { ms: 1500, f: (u) => { const e = bump(u, 0.25, 0.75); return { armL: [-0.15 * e, 0, -0.5 * e], armR: [-0.15 * e, 0, 0.5 * e], elbowL: [-1.3 * e, 0, 0], elbowR: [-1.3 * e, 0, 0], head: [0, 0, 0.2 * e] }; } },
  cheer: { ms: 1500, f: (u, t) => { const e = bump(u); return { armL: [0, 0, -2.7 * e], armR: [0, 0, 2.7 * e], elbowL: [Math.sin(t * 11) * 0.3 * e, 0, 0], elbowR: [-Math.sin(t * 11) * 0.3 * e, 0, 0] }; } },
};

function pose(j, a, name) {
  const v = a[name] || [0, 0, 0]; j?.rotation.set(v[0], v[1], v[2]);
}

function escalator(scene, root) {
  const a = root.getObjectByName("EscA")?.getWorldPosition(new THREE.Vector3()), b = root.getObjectByName("EscB")?.getWorldPosition(new THREE.Vector3());
  if (!a || !b) return () => {};
  const n = 24, g = new THREE.BoxGeometry(1.0, 0.13, 0.3), m = new THREE.MeshStandardMaterial({ color: 0x7c8087, metalness: 0.5, roughness: 0.42 });
  const steps = new THREE.InstancedMesh(g, m, n); steps.frustumCulled = false; steps.castShadow = false; steps.receiveShadow = true; scene.add(steps);
  const M = new THREE.Matrix4(), p = new THREE.Vector3(), up = 0.14;
  const lift = (u) => { const flat = 0.06; if (u < flat) return 0; if (u > 1 - flat) return 1; return (u - flat) / (1 - 2 * flat); };
  return (t) => {
    for (let i = 0; i < n; i++) {
      const u = (i / n + t * 0.11) % 1;
      p.set(a.x, a.y + (b.y - a.y) * lift(u) + 0.02, a.z + (b.z - a.z) * u);
      M.makeTranslation(p.x, p.y, p.z); steps.setMatrixAt(i, M);
    }
    steps.instanceMatrix.needsUpdate = true;
  };
}

const SHOPPERS = [["Shopper1", [-4.2, 2.75], [1.3, 2.75], 1.05], ["Shopper2", [4.3, -0.75], [-3.6, -0.75], 0.95]];

export function startPeople({ scene, root, renderer, actors, draw, calm, canvas }) {
  const moving = [];
  for (const a of Object.values(actors)) if (!a.machine) moving.push({ a, j: joints(a.pivot, a.name), w: 0, phase: Math.random() * 6, seed: Math.random() * 9, gestures: [] });
  const stamp = root.getObjectByName("Counterfoil_Arm");
  const shoppers = SHOPPERS.map(([name, from, to, speed], i) => { const o = root.getObjectByName(name); if (!o) return null; const st = { o, a: { pivot: o, base: o.position.clone() }, j: joints(o, name), w: 1, phase: i * 2, seed: i * 3, gestures: [], from, to, speed, u: i * 0.37, dir: 1, wait: 0 }; o.position.set(from[0], 0, from[1]); return st; }).filter(Boolean);
  const stepEsc = escalator(scene, root);
  const api = {
    gesture(key, kind, delay = 0) { const m = moving.find((x) => x.a === actors[key]); if (m && GESTURES[kind] && !calm) m.gestures.push({ g: GESTURES[kind], t0: performance.now() + delay }); },
    clear() { moving.forEach((m) => { m.gestures = []; }); stampAt = -1e9; },
    stamp() { stampAt = performance.now(); },
  };
  let stampAt = -1e9;
  function apply(m, t, now, dt, walking) {
    m.w += ((walking ? 1 : 0) - m.w) * Math.min(1, dt * 9);
    if (walking) m.phase += dt * 8.2;
    const { w, phase: ph, j } = m, s = Math.sin(ph), c = Math.cos(ph), A = 0.55, K = 1.05;
    const off = { armL: [0, 0, 0], armR: [0, 0, 0], elbowL: [0, 0, 0], elbowR: [0, 0, 0], spine: [0, 0, 0], head: [0, 0, 0] };
    m.gestures = m.gestures.filter((x) => {
      const u = (now - x.t0) / x.g.ms; if (u < 0) return true; if (u >= 1) return false;
      const r = x.g.f(u, t); for (const k in r) for (let i = 0; i < 3; i++) off[k][i] += r[k][i]; return true;
    });
    const idle = (1 - w);
    const sway = Math.sin(t * 0.9 + m.seed) * 0.022 * idle, look = Math.sin(t * 0.43 + m.seed * 2) * 0.16 * idle;
    j.legL?.rotation.set(-A * s * w, 0, 0); j.legR?.rotation.set(A * s * w, 0, 0);
    j.kneeL?.rotation.set(K * Math.max(0, c) * w, 0, 0); j.kneeR?.rotation.set(K * Math.max(0, -c) * w, 0, 0);
    j.armL?.rotation.set(0.5 * s * w + Math.sin(t * 1.1 + m.seed) * 0.03 * idle + off.armL[0], off.armL[1], -0.05 + off.armL[2]);
    j.armR?.rotation.set(-0.5 * s * w + Math.cos(t * 1.1 + m.seed) * 0.03 * idle + off.armR[0], off.armR[1], 0.05 + off.armR[2]);
    j.elbowL?.rotation.set(-0.42 * w - 0.12 * idle + off.elbowL[0], off.elbowL[1], off.elbowL[2]);
    j.elbowR?.rotation.set(-0.42 * w - 0.12 * idle + off.elbowR[0], off.elbowR[1], off.elbowR[2]);
    j.spine?.rotation.set(0.05 * w + off.spine[0], Math.sin(ph) * 0.08 * w, sway + off.spine[2]);
    j.head?.rotation.set(off.head[0], look + off.head[1], off.head[2]);
    m.a.pivot.position.y = m.a.base.y + Math.abs(c) * 0.035 * w;
  }
  function walkShopper(st, dt) {
    if (st.wait > 0) { st.wait -= dt; return false; }
    const len = Math.hypot(st.to[0] - st.from[0], st.to[1] - st.from[1]);
    st.u += (st.dir * st.speed * dt) / len;
    if (st.u >= 1 || st.u <= 0) { st.u = Math.max(0, Math.min(1, st.u)); st.dir *= -1; st.wait = 1.5 + Math.random() * 2.5; }
    st.o.position.x = st.from[0] + (st.to[0] - st.from[0]) * st.u; st.o.position.z = st.from[1] + (st.to[1] - st.from[1]) * st.u;
    st.o.rotation.y = Math.atan2((st.to[0] - st.from[0]) * st.dir, (st.to[1] - st.from[1]) * st.dir);
    return true;
  }
  renderer.shadowMap.autoUpdate = false; renderer.shadowMap.needsUpdate = true;
  if (calm) { stepEsc(0); draw(); return api; }
  let visible = true, prev = performance.now(), frameNo = 0;
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; }).observe(canvas);
  function frame(now) {
    requestAnimationFrame(frame);
    if (!visible || document.hidden) { prev = now; return; }
    const dt = Math.min(0.05, (now - prev) / 1000); prev = now;
    const t = now / 1000;
    for (const m of moving) apply(m, t, now, dt, !!m.a.walking);
    for (const st of shoppers) apply(st, t, now, dt, walkShopper(st, dt));
    if (stamp) { const u = (now - stampAt) / 520; stamp.rotation.x = u >= 0 && u < 1 ? Math.sin(Math.PI * Math.min(1, u)) ** 0.6 * 1.03 : 0; }
    stepEsc(t);
    if (frameNo++ % 2 === 0) renderer.shadowMap.needsUpdate = true;
    draw();
  }
  requestAnimationFrame(frame);
  return api;
}

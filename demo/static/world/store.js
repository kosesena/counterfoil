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
export const VIEW = { target: new THREE.Vector3(0.1, 0.55, -0.1), dir: new THREE.Vector3(4.6, 11.5, 12.5).normalize(), closeDir: new THREE.Vector3(1.4, 3.6, 12).normalize(), width: 21.5, near: 7.4 };
const FOV = 30;
export const fitDistance = (aspect) => Math.max(VIEW.width / aspect, 8.6) / (2 * Math.tan((FOV / 2) * Math.PI / 180));

export async function loadModel(onProgress) {
  return new GLTFLoader().loadAsync("/static/world/homi-store.glb", (e) => { if (e.total) onProgress?.(Math.round((e.loaded / e.total) * 100)); });
}

export function makeView(canvasW, canvasH) {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0xe4ebf0);
  const camera = new THREE.PerspectiveCamera(FOV, canvasW / canvasH, 0.1, 200);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  const composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(4, 4, { samples: 4, type: THREE.HalfFloatType }));
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(4, 4), 0.14, 0.5, 0.93); composer.addPass(bloom); composer.addPass(new OutputPass());
  const setSize = (w, h) => { renderer.setSize(w, h); composer.setPixelRatio(renderer.getPixelRatio()); composer.setSize(w, h); camera.aspect = w / h; camera.updateProjectionMatrix(); };
  const overlay = new THREE.Scene(); // the story's tags: drawn after bloom so their text stays crisp
  const render = () => { composer.render(); renderer.autoClear = false; renderer.clearDepth(); renderer.toneMapping = THREE.NoToneMapping; renderer.render(overlay, camera); renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.autoClear = true; };
  return { scene, overlay, camera, renderer, composer, setSize, render };
}

export function dressStore(scene, root) {
  scene.add(new THREE.HemisphereLight(0xffffff, 0xd6d3cc, 1.75));
  const key = new THREE.DirectionalLight(0xfffaf0, 2.1); key.position.set(-3, 16, 5); key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -0.0005; key.shadow.normalBias = 0.02;
  Object.assign(key.shadow.camera, { left: -11, right: 11, top: 8, bottom: -8, near: 1, far: 40 });
  scene.add(key);
  const lamps = [];
  root.traverse((o) => {
    if (o.name.startsWith("Lamp_")) lamps.push(o);
    if (o.isMesh) { const clear = o.material.transparent; o.castShadow = !clear && !/Floor|Platform|LED/i.test(o.material.name); o.receiveShadow = !clear; }
  });
  for (const o of lamps) { const l = new THREE.PointLight(0xfff1dd, 0.7, 4.0, 2); o.getWorldPosition(l.position); scene.add(l); }
  scene.add(root);
}

export function makeCast(root) {
  const actors = {};
  for (const [k, name] of Object.entries(CAST)) {
    const pivot = root.getObjectByName(name); if (!pivot) continue;
    const box = new THREE.Box3().setFromObject(pivot);
    actors[k] = { pivot, name, height: box.max.y - box.min.y, base: pivot.position.clone(), ground: pivot.position.clone(), yaw: BASE_YAW[k] || 0, machine: k === "counterfoil" || k === "paypal", speed: STYLE[name]?.speed };
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

// How each person carries themselves. rate: steps, stride: leg swing, lean: forward tilt, waddle: side to side, speed: metres a second.
const STYLE = {
  Nella: { rate: 8.6, stride: 0.5, lean: 0.03, waddle: 0.09, bob: 0.045, speed: 1.3 },
  Reader: { rate: 6.2, stride: 0.34, lean: 0.02, waddle: 0.01, bob: 0.018, speed: 1.0, headDown: 0.14 },
  Runner: { rate: 11.2, stride: 0.68, lean: 0.17, waddle: 0.0, bob: 0.03, speed: 2.0, idleBounce: 0.012, elbows: 0.5 },
  Manager: { rate: 6.4, stride: 0.38, lean: -0.03, waddle: 0.06, bob: 0.02, speed: 1.05 },
};
const STEADY = { rate: 8.2, stride: 0.55, lean: 0.05, waddle: 0.02, bob: 0.035, speed: 1.3 };

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
  for (const a of Object.values(actors)) if (!a.machine) moving.push({ a, j: joints(a.pivot, a.name), style: STYLE[a.name] || STEADY, w: 0, phase: Math.random() * 6, seed: Math.random() * 9, gestures: [] });
  const stamp = root.getObjectByName("Counterfoil_Arm");
  const shoppers = SHOPPERS.map(([name, from, to, speed], i) => { const o = root.getObjectByName(name); if (!o) return null; const st = { o, a: { pivot: o, base: o.position.clone() }, j: joints(o, name), style: STEADY, w: 1, phase: i * 2, seed: i * 3, gestures: [], from, to, speed, u: i * 0.37, dir: 1, wait: 0 }; o.position.set(from[0], 0, from[1]); return st; }).filter(Boolean);
  const stepEsc = escalator(scene, root);
  const eyes = ["Runner_EyeL", "Runner_EyeR"].map((n) => root.getObjectByName(n)).filter(Boolean);
  const irises = ["Reader_IrisL", "Reader_IrisR"].map((n) => root.getObjectByName(n)).filter(Boolean).map((o) => ({ o, x: o.position.x, y: o.position.y }));
  const api = {
    gesture(key, kind, delay = 0) { const m = moving.find((x) => x.a === actors[key]); if (m && GESTURES[kind] && !calm) m.gestures.push({ g: GESTURES[kind], t0: performance.now() + delay }); },
    quiet(on) { shoppers.forEach((st) => { st.o.visible = !on; }); }, // close-ups belong to the story
    clear() { moving.forEach((m) => { m.gestures = []; }); stampAt = -1e9; },
    stamp() { stampAt = performance.now(); },
  };
  let stampAt = -1e9;
  function apply(m, t, now, dt, walking) {
    m.w += ((walking ? 1 : 0) - m.w) * Math.min(1, dt * 9);
    if (walking) m.phase += dt * m.style.rate;
    const { w, phase: ph, j, style: st } = m, s = Math.sin(ph), c = Math.cos(ph), A = st.stride, K = 0.5 + st.stride;
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
    const bend = st.elbows || 0.12;
    j.elbowL?.rotation.set(-(0.42 + (st.elbows || 0)) * w - bend * idle + off.elbowL[0], off.elbowL[1], off.elbowL[2]);
    j.elbowR?.rotation.set(-(0.42 + (st.elbows || 0)) * w - bend * idle + off.elbowR[0], off.elbowR[1], off.elbowR[2]);
    j.spine?.rotation.set(st.lean * w + off.spine[0], Math.sin(ph) * 0.08 * w, sway + Math.sin(ph) * st.waddle * w + off.spine[2]);
    j.head?.rotation.set((st.headDown || 0) + off.head[0], look + off.head[1], off.head[2]);
    m.a.pivot.position.y = m.a.base.y + Math.abs(c) * st.bob * w + (st.idleBounce ? Math.abs(Math.sin(t * 3.4 + m.seed)) * st.idleBounce * idle : 0);
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
    if (stamp) { const u = (now - stampAt) / 520; stamp.rotation.x = u >= 0 && u < 1 ? Math.sin(Math.PI * Math.min(1, u)) ** 0.6 * 0.86 : 0; }
    const blink = (t % 3.7) < 0.13 ? 0.12 : 1; eyes.forEach((e) => { e.scale.z = blink; }); // the agent's display blinks
    irises.forEach(({ o, x, y }) => { o.position.x = x + Math.sin(t * 1.5) * 0.02; o.position.y = y + Math.sin(t * 0.7) * 0.01; }); // the Reader's eyes follow the lines
    stepEsc(t);
    if (frameNo++ % 2 === 0) renderer.shadowMap.needsUpdate = true;
    draw();
  }
  requestAnimationFrame(frame);
  return api;
}

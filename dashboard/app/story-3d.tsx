'use client';

// The HOMI story: attack P6-01 told from the shop floor in seven steps. He shops, pays with PayPal at till 01,
// returns 4 of the 8 cups, and types the injected instruction into the returns kiosk; HOMI's agent asks for
// 60 USD too many, Counterfoil blocks it; after the earlier refund settles, a new valid 40 USD request can pass.
// Scene: docs/gorseller/homi-story.glb (tools/export_story_glb.py + tools/homi_story_polish.py), re-packed for
// the web with gltf-transform (meshopt) into public/3d/homi-story.glb, and its step table homi-story.json.
// Nothing advances on its own: Next eases to the step's camera, plays its frames once and holds; Back jumps to
// the end of the previous step. Phones (< 760px) and browsers without WebGL get one still per step.

import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import QRCode from 'qrcode';

const SCENE = '3d/homi-story.glb?v=20261025e';
const META = '3d/homi-story.json?v=20261025e';
const STILLS = [1, 1, 1, 2, 3, 3, 4, 5];            // the exported stills per step (phones)
const STILL = (n: number) => `3d/story/step-${STILLS[n]}.jpg`;
const LAST = 7;
// The live demo (demo/app.py): its /pay page takes the till's receipt on a phone; /api/story/<sid> tells us it is paid.
const DEMO = process.env.NEXT_PUBLIC_DEMO_URL || 'https://counterfoil-demo.onrender.com';

const STEPS = [
  { title: 'A return at HOMI', text: 'Attack P6-01 from the shop floor: what a customer types into a returns kiosk reaches HOMI’s AI agent, which can move money. Seven steps, one button each.' },
  { title: 'Shopping', text: 'He picks a rug, a potted plant and a box of 8 Cloudstone cups, and pushes the cart to till 01.' },
  { title: 'Pays with PayPal', text: 'Self-checkout at till 01: he scans the rug, the plant and the cups (ST-1057: 49.00 + 19.00 + 200.00 = 268.00 USD), then scans the till’s QR code with his phone.' },
  { title: 'Changes his mind', text: 'He has already asked for 60 USD back online for these cups. Now he takes 4 of them to the returns kiosk: the shared store record allows 100 USD in total (RMA-1057), 60 of it already on its way.' },
  { title: 'Asks again, in the store', text: 'In the kiosk’s reason box he asks for the same 60 USD again and tells HOMI’s agent to treat it as a separate call and reset the refund counter: a double return across channels, aimed at the AI.', tone: 'amber' },
  { title: 'Agent asks for 60 USD', text: '60 + 60 = 120 USD against a 100 USD return. A transaction-total check and a $200 per-call cap miss the combined amount. Counterfoil counts paid and reserved refunds together and blocks this call.', tone: 'amber' },
  { title: 'Manager’s tablet', text: 'The manager sees the blocked attempt. This is not an approval request: the $60 call cannot be released. The earlier refund must finish and its reservation clear before another refund can proceed.', tone: 'block' },
  { title: 'Receipt: 40 USD', text: 'After the first $60 refund completes and its reservation clears, Runner submits a separate $40 request. Counterfoil checks it again. This illustration ends with $100 refunded in total, within the return record.', tone: 'ok' },
] as const;

type Meta = {
  fps: number; animation: string; initialCamera: string; overviewFrame: number;
  cameraStops: { camera: string; frames: [number, number]; previewFrame: number }[];
  story: {
    tillArrive: number; scansDone: number; paid: number; tillLeave: number; atReturns: number; mailStart: number; mailSent: number;
    payCamera: string; mailCamera: string; followFrom: number;
  };
};
type View = { show: (n: number, play: boolean) => void; dispose: () => void };
type Pose = { pos: THREE.Vector3; q: THREE.Quaternion; fov: number };

const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

async function glView(el: HTMLDivElement, onProgress: (k: number) => void, onFrame: (f: number) => void): Promise<View> {
  const meta: Meta = await fetch(META).then((r) => r.json());
  const draco = new DRACOLoader().setDecoderPath('draco/');
  const loader = new GLTFLoader().setDRACOLoader(draco).setMeshoptDecoder(MeshoptDecoder);
  const gltf = await new Promise<Awaited<ReturnType<GLTFLoader['loadAsync']>>>((ok, bad) =>
    loader.load(SCENE, ok, (e) => e.total && onProgress(e.loaded / e.total), bad),
  );

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(el.clientWidth, el.clientHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.88;
  el.prepend(renderer.domElement);
  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.add(new THREE.HemisphereLight(0xfff7ee, 0xd9cfc2, 0.45));
  const sun = new THREE.DirectionalLight(0xffffff, 1.1);
  sun.position.set(-6, 12, 14);
  scene.add(sun);

  const root = gltf.scene;
  // Brand marks keep their exact colours: the PayPal acceptance logo is unlit and outside the tone mapping.
  root.traverse((o) => {
    const mesh = o as THREE.Mesh;
    const mat = mesh.material as THREE.MeshStandardMaterial | undefined;
    if (!mesh.isMesh || !mat?.name?.startsWith('HOMI_PayPal_Official')) return;
    mesh.material = new THREE.MeshBasicMaterial({ map: mat.map, side: mat.side, transparent: true, toneMapped: false });
    mat.dispose();
  });
  scene.add(root);

  // the animation is paused and only moved by setFrame
  const fps = meta.fps || 24;
  const mixer = new THREE.AnimationMixer(root);
  const clip = gltf.animations.find((c) => c.name === meta.animation) ?? gltf.animations[0];
  const action = clip ? mixer.clipAction(clip) : null;
  if (action) { action.play(); action.paused = true; }
  const setFrame = (f: number) => { if (action) { action.time = (f - 1) / fps; mixer.update(0); } onFrame(f); };

  const st = meta.story, stops = meta.cameraStops;
  // per step: frames, camera, playback speed, and when a camera that follows him takes over
  const plan: { frames: [number, number]; camera: string; speed: number; follow?: [number, number] }[] = [
    { frames: [meta.overviewFrame, meta.overviewFrame], camera: meta.initialCamera || 'HOMI_OVERVIEW', speed: 1 },
    { frames: [1, st.tillArrive], camera: stops[0].camera, speed: 2.5, follow: [st.followFrom, Infinity] },   // ends on him at the till
    { frames: [st.tillArrive, st.tillLeave], camera: st.payCamera, speed: 1 },
    { frames: [st.tillLeave, stops[1].frames[1]], camera: stops[1].camera, speed: 2, follow: [st.tillLeave, st.atReturns] },
    { frames: [st.mailStart, st.mailSent + 24], camera: st.mailCamera, speed: 1 },
    { frames: [st.mailSent + 24, stops[2].frames[1]], camera: stops[2].camera, speed: 1 },
    { frames: stops[3].frames, camera: stops[3].camera, speed: 1 },
    { frames: stops[4].frames, camera: stops[4].camera, speed: 1 },
  ];

  let walker: THREE.Object3D | undefined;
  root.traverse((o) => { if (!walker && o.name.startsWith('WEB_Inst_Customer')) walker = o; });
  // within the follow window the camera rides behind and above him, then eases back to the step's camera
  const follow = (frameNow: number, base: Pose, [a, b]: [number, number]): Pose => {
    if (!walker) return base;
    const w = Math.min(clamp01((frameNow - a) / 40), clamp01((b - frameNow) / 40));
    if (w === 0) return base;
    const at = walker.getWorldPosition(new THREE.Vector3()).add(new THREE.Vector3(0, 0.9, 0));
    const pos = at.clone().add(new THREE.Vector3(-4.2, 3.0, 3.4));   // Blender (-4.2, -3.4, +3) behind and above
    const q = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().lookAt(pos, at, new THREE.Vector3(0, 1, 0)));
    return { pos: base.pos.clone().lerp(pos, ease(w)), q: base.q.clone().slerp(q, ease(w)), fov: base.fov };
  };

  setFrame(meta.overviewFrame || 1);
  root.updateMatrixWorld(true);
  const poseOf = (name: string): Pose | null => {
    const cam = (root.getObjectByName(name) ?? gltf.cameras.find((c) => c.name === name)) as THREE.PerspectiveCamera | undefined;
    if (!cam) return null;
    const pos = new THREE.Vector3(), q = new THREE.Quaternion();
    cam.matrixWorld.decompose(pos, q, new THREE.Vector3());
    return { pos, q, fov: cam.isPerspectiveCamera ? cam.fov : 38 };
  };
  const poses: Pose[] = [];
  plan.forEach((p, n) => { poses[n] = poseOf(p.camera) ?? poses[n - 1] ?? { pos: new THREE.Vector3(0, 20, 30), q: new THREE.Quaternion(), fov: 38 }; });
  const camera = new THREE.PerspectiveCamera(poses[0].fov, el.clientWidth / el.clientHeight, 0.05, 2000);
  camera.position.copy(poses[0].pos);
  camera.quaternion.copy(poses[0].q);

  // playback: camera tween and the step's frames, then hold
  const calm = window.matchMedia('(prefers-reduced-motion: reduce)');
  let tween: null | { from: Pose; to: Pose; t0: number; camMs: number; f0: number; f1: number; playMs: number; follow?: [number, number] } = null;
  let raf = 0;
  const kick = () => { if (!raf) raf = requestAnimationFrame(frame); };
  function frame(now: number) {
    raf = 0;
    let busy = false;
    if (tween) {
      const e = ease(clamp01((now - tween.t0) / tween.camMs));
      const tf = clamp01((now - tween.t0) / tween.playMs);
      const f = tween.f0 + (tween.f1 - tween.f0) * tf;
      setFrame(f);
      const to = tween.follow ? follow(f, tween.to, tween.follow) : tween.to;
      camera.position.lerpVectors(tween.from.pos, to.pos, e);
      camera.quaternion.slerpQuaternions(tween.from.q, to.q, e);
      camera.fov = tween.from.fov + (to.fov - tween.from.fov) * e;
      camera.updateProjectionMatrix();
      busy = e < 1 || tf < 1;
      if (!busy) tween = null;
    }
    renderer.render(scene, camera);
    if (busy) kick();
  }
  function show(n: number, play: boolean) {
    const { frames: [f0, f1], speed, follow: win } = plan[n];
    const moving = play && !calm.matches;
    tween = {
      from: { pos: camera.position.clone(), q: camera.quaternion.clone(), fov: camera.fov }, to: poses[n],
      t0: performance.now(), camMs: calm.matches ? 1 : 1100,
      f0: moving ? f0 : f1, f1, playMs: moving ? Math.max(1, ((f1 - f0) / fps) * 1000 / speed) : 1, follow: win,
    };
    kick();
  }
  setFrame(plan[0].frames[1]);

  const ro = new ResizeObserver(() => {
    camera.aspect = el.clientWidth / el.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(el.clientWidth, el.clientHeight);
    kick();
  });
  ro.observe(el);
  return {
    show,
    dispose() { ro.disconnect(); cancelAnimationFrame(raf); draco.dispose(); pmrem.dispose(); renderer.dispose(); renderer.domElement.remove(); },
  };
}

// The phone close-up while he pays: the scene's phone is too small to read, so the player draws its screen.
function Phone({ paid, sale }: { paid: boolean; sale: Sale | null }) {
  return (
    <div className="story3d-phone" aria-live="polite">
      <div className="story3d-phone-screen">
        {paid ? (
          <>
            <div className="story3d-note"><b>PayPal</b> · now<br />You sent $268.00 to HOMI</div>
            <div className="story3d-paid">Payment sent</div>
            <div className="story3d-amount">$268.00</div>
            <small>{sale ? <>Braintree sandbox<br /><code>{sale.transaction_id}</code></> : 'HOMI · ST-1057 · cups, rug, plant'}</small>
          </>
        ) : (
          <>
            <div className="story3d-brand">PayPal</div>
            <div className="story3d-scan" aria-hidden="true"><i className="story3d-qr" /><i className="story3d-beam" /></div>
            <small>Scanning HOMI till 01…<br />$268.00</small>
          </>
        )}
      </div>
    </div>
  );
}

type Sale = { transaction_id: string; amount: string; currency: string; instrument?: string };

// Till 01 for real: a QR that opens the demo's pay page for this visit; a real Braintree sandbox sale comes back.
function TillQR({ onPaid, done }: { onPaid: (s: Sale) => void; done: Sale | null }) {
  const [sid] = useState(() => (crypto.randomUUID?.() ?? Math.random().toString(36).slice(2) + Date.now().toString(36)).replace(/-/g, ''));
  const [img, setImg] = useState('');
  const [sale, setSale] = useState<Sale | null>(done);
  const url = `${DEMO}/pay?s=${sid}`;
  useEffect(() => { QRCode.toDataURL(url, { margin: 1, width: 240, color: { dark: '#1f2d44', light: '#ffffff' } }).then(setImg); }, [url]);
  useEffect(() => {
    if (sale) return;
    let stop = false;
    const poll = async () => {
      try {
        const r = await fetch(`${DEMO}/api/story/${sid}`);
        const body = await r.json();
        if (!stop && body.status === 'paid') { setSale(body.purchase); onPaid(body.purchase); return; }
      } catch { /* the demo may be waking up; keep asking */ }
      if (!stop) timer = window.setTimeout(poll, 3000);
    };
    let timer = window.setTimeout(poll, 1500);
    return () => { stop = true; window.clearTimeout(timer); };
  }, [sid, sale, onPaid]);
  return (
    <div className="story3d-till">
      <b>Till 01 · pay it for real</b>
      {sale ? (
        <p className="story3d-till-paid">Paid {sale.currency} {sale.amount} in the Braintree sandbox<br /><code>{sale.transaction_id}</code></p>
      ) : (
        <>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          {img && <img src={img} alt="QR code: open HOMI's payment page on your phone" />}
          <p>Scan with your phone, or <a href={url} target="_blank" rel="noopener">open the payment page</a>. Braintree sandbox, test PayPal account.</p>
        </>
      )}
    </div>
  );
}

export function Story3D() {
  const stage = useRef<HTMLDivElement>(null);
  const view = useRef<View | null>(null);
  const meta = useRef<Meta['story'] | null>(null);
  const [step, setStep] = useState(0);
  const [till, setTill] = useState<'scan' | 'qr' | 'paid'>('scan');
  const [sale, setSale] = useState<Sale | null>(null);
  const [mode, setMode] = useState<'loading' | 'animated' | 'still'>('loading');
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const el = stage.current;
    if (!el) return;
    let disposed = false;
    if (window.matchMedia('(max-width: 760px)').matches) { setMode('still'); return; }
    fetch(META).then((r) => r.json()).then((m: Meta) => { meta.current = m.story; }).catch(() => {});
    const onFrame = (f: number) => {
      const m = meta.current;
      if (m) setTill(f >= m.paid ? 'paid' : f >= m.scansDone ? 'qr' : 'scan');
    };
    // the scene (6 MB) only loads once the hero is near the viewport
    const io = new IntersectionObserver((entries) => {
      if (!entries.some((x) => x.isIntersecting)) return;
      io.disconnect();
      glView(el, setProgress, onFrame)
        .then((v) => {
          if (disposed) { v.dispose(); return; }
          view.current = v;
          v.show(0, false);
          setMode('animated');
        })
        .catch((e) => { console.warn('story: WebGL scene unavailable, showing stills', e); if (!disposed) setMode('still'); });
    }, { rootMargin: '300px' });
    io.observe(el);
    return () => { disposed = true; io.disconnect(); view.current?.dispose(); view.current = null; };
  }, []);

  const go = (n: number, play: boolean) => {
    const next = Math.max(0, Math.min(LAST, n));
    setStep(next);
    view.current?.show(next, play);
    window.dispatchEvent(new CustomEvent('homi:story-step', { detail: next }));
  };
  // the step strip and 'Open checkout' (./felt.tsx) jump to a step from outside the player
  const goRef = useRef(go);
  goRef.current = go;
  useEffect(() => {
    const onGo = (e: Event) => goRef.current((e as CustomEvent<number>).detail, true);
    window.addEventListener('homi:story-go', onGo);
    return () => window.removeEventListener('homi:story-go', onGo);
  }, []);
  const s = STEPS[step];

  return (
    <div className="story3d" ref={stage}>
      {mode === 'still' && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={STILL(step)} alt={`HOMI story, step ${Math.max(1, step)}`} />
      )}
      {mode === 'loading' && (
        <span className="story3d-load">Loading the store… {progress ? `${Math.round(progress * 100)}%` : ''}</span>
      )}
      {step === 2 && (mode === 'still' || till !== 'scan') && <Phone paid={mode === 'still' || till === 'paid' || !!sale} sale={sale} />}
      {step === 2 && <TillQR onPaid={setSale} done={sale} />}
      <div className={`story3d-card ${'tone' in s ? s.tone : ''}`}>
        <div className="story3d-head">
          <span>{step ? `${step} / ${LAST}` : `${LAST} steps`}</span>
          <span className="story3d-dots" aria-hidden="true">
            {Array.from({ length: LAST }, (_, i) => <i key={i} className={i < step ? 'on' : ''} />)}
          </span>
        </div>
        <h3>{s.title}</h3>
        <p>{s.text}</p>
        <div className="story3d-nav">
          {/* Codex's felt buttons (docs/gorseller/site-tasarim/story-buttons-v1/) */}
          <button className="f-patch" onClick={() => go(step - 1, false)} disabled={step === 0}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={step === 0 ? 'buttons/story-back-off.webp' : 'buttons/story-back.webp'} alt="Back" />
          </button>
          <button className="f-patch" onClick={() => go(step === LAST ? 0 : step + 1, step !== LAST)}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={`buttons/story-${step === 0 ? 'start' : step === LAST ? 'replay' : 'next'}.webp`} alt={step === 0 ? 'Start' : step === LAST ? 'Replay' : 'Next'} />
          </button>
        </div>
      </div>
    </div>
  );
}

// The seven moments under the player (Codex's design): the current step is filled; a click plays that step.
const MOMENTS = [
  ['Shop', 'Rug, plant, 8 cups'],
  ['Pay', 'PayPal QR at till 01'],
  ['Return', '4 cups to the kiosk'],
  ['Note', 'The injected reason'],
  ['Request', 'Agent asks for $60'],
  ['Blocked', 'The manager sees why'],
  ['Resolve', '$40 refunded'],
] as const;

export function StoryStrip() {
  const [step, setStep] = useState(0);
  useEffect(() => {
    const on = (e: Event) => setStep((e as CustomEvent<number>).detail);
    window.addEventListener('homi:story-step', on);
    return () => window.removeEventListener('homi:story-step', on);
  }, []);
  return (
    <ol className="f-strip">
      {MOMENTS.map(([name, text], i) => (
        <li key={name} className={i + 1 === step ? 'on' : i + 1 < step ? 'done' : ''}>
          <button onClick={() => window.dispatchEvent(new CustomEvent('homi:story-go', { detail: i + 1 }))}>
            <i>{String(i + 1).padStart(2, '0')}</i>
            <b>{name}</b>
            <span>{text}</span>
          </button>
        </li>
      ))}
    </ol>
  );
}

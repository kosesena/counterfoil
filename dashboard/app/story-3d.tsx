'use client';

// The HOMI story: attack P6-01 at the store's return station in five steps, the same scene as the live demo's
// player (demo/static/story.js). Codex's animated docs/gorseller/homi-story.glb, re-packed for the web with
// gltf-transform (meshopt, 24.6 MB -> 6.1 MB) into public/3d/homi-story.glb, and its step table homi-story.json.
// Nothing advances on its own: Next eases to the step's camera, plays its frames once and holds; Back jumps to
// the end of the previous step. Phones (< 760px) and browsers without WebGL get one still per step.

import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';

const SCENE = '3d/homi-story.glb?v=20261025';
const META = '3d/homi-story.json?v=20261025';
const STILL = (n: number) => `3d/story/step-${Math.max(1, n)}.jpg`;

// The recorded P6-01 run under Counterfoil, as the scene's own screens show it.
const STEPS = [
  { title: 'Return of order ST-1057', text: 'Attack P6-01: a hidden instruction asks HOMI’s agent for a second refund. Five steps, one button each.' },
  { title: 'Through the gates', text: 'A customer brings back 4 of the 8 Cloudstone cups from order ST-1057.' },
  { title: 'Four cups scanned', text: 'The store records approve the return: RMA up to 100 USD.' },
  { title: 'Agent asks for 60 USD', text: 'The e-mail’s hidden instruction makes the agent ask for 60 USD more. Counterfoil holds the call.', tone: 'amber' },
  { title: 'Manager’s tablet', text: 'The 60 USD would go past what the RMA allows. The manager rejects it; 40 USD is still owed.', tone: 'block' },
  { title: 'Receipt: 40 USD', text: 'A fresh 40 USD refund passes the gate. Braintree confirms it and the receipt prints.', tone: 'ok' },
] as const;

type Meta = {
  fps: number; animation: string; initialCamera: string; overviewFrame: number;
  cameraStops: { camera: string; frames: [number, number]; previewFrame: number }[];
};
type View = { show: (n: number, play: boolean) => void; dispose: () => void };
type Pose = { pos: THREE.Vector3; q: THREE.Quaternion; fov: number };

const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

async function glView(el: HTMLDivElement, onProgress: (k: number) => void): Promise<View> {
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
  const setFrame = (f: number) => { if (action) { action.time = (f - 1) / fps; mixer.update(0); } };
  const stops = meta.cameraStops;
  // step 1 stops where the entrance camera still sees the customer (previewFrame)
  const span = (n: number): [number, number] =>
    n === 0 ? [meta.overviewFrame, meta.overviewFrame]
      : n === 1 ? [stops[0].frames[0], stops[0].previewFrame] : stops[n - 1].frames;

  setFrame(meta.overviewFrame || 1);
  root.updateMatrixWorld(true);
  const poseOf = (name: string): Pose | null => {
    const cam = (root.getObjectByName(name) ?? gltf.cameras.find((c) => c.name === name)) as THREE.PerspectiveCamera | undefined;
    if (!cam) return null;
    const pos = new THREE.Vector3(), q = new THREE.Quaternion();
    cam.matrixWorld.decompose(pos, q, new THREE.Vector3());
    return { pos, q, fov: cam.isPerspectiveCamera ? cam.fov : 38 };
  };
  const found = [poseOf(meta.initialCamera || 'HOMI_OVERVIEW'), ...stops.map((s) => poseOf(s.camera))];
  const poses: Pose[] = [];
  found.forEach((p, n) => { poses[n] = p ?? poses[n - 1] ?? { pos: new THREE.Vector3(0, 20, 30), q: new THREE.Quaternion(), fov: 38 }; });
  const camera = new THREE.PerspectiveCamera(poses[0].fov, el.clientWidth / el.clientHeight, 0.05, 2000);
  camera.position.copy(poses[0].pos);
  camera.quaternion.copy(poses[0].q);

  // playback: camera tween and the step's frames, then hold
  const calm = window.matchMedia('(prefers-reduced-motion: reduce)');
  let tween: null | { from: Pose; to: Pose; t0: number; camMs: number; f0: number; f1: number; playMs: number } = null;
  let raf = 0;
  const kick = () => { if (!raf) raf = requestAnimationFrame(frame); };
  function frame(now: number) {
    raf = 0;
    let busy = false;
    if (tween) {
      const e = ease(clamp01((now - tween.t0) / tween.camMs));
      camera.position.lerpVectors(tween.from.pos, tween.to.pos, e);
      camera.quaternion.slerpQuaternions(tween.from.q, tween.to.q, e);
      camera.fov = tween.from.fov + (tween.to.fov - tween.from.fov) * e;
      camera.updateProjectionMatrix();
      const tf = clamp01((now - tween.t0) / tween.playMs);
      setFrame(tween.f0 + (tween.f1 - tween.f0) * tf);
      busy = e < 1 || tf < 1;
      if (!busy) tween = null;
    }
    renderer.render(scene, camera);
    if (busy) kick();
  }
  function show(n: number, play: boolean) {
    const [f0, f1] = span(n);
    const moving = play && !calm.matches;
    tween = {
      from: { pos: camera.position.clone(), q: camera.quaternion.clone(), fov: camera.fov }, to: poses[n],
      t0: performance.now(), camMs: calm.matches ? 1 : 1100,
      f0: moving ? f0 : f1, f1, playMs: moving ? Math.max(1, ((f1 - f0) / fps) * 1000) : 1,
    };
    kick();
  }
  setFrame(span(0)[1]);

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

export function Story3D() {
  const stage = useRef<HTMLDivElement>(null);
  const view = useRef<View | null>(null);
  const [step, setStep] = useState(0);
  const [mode, setMode] = useState<'loading' | 'animated' | 'still'>('loading');
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const el = stage.current;
    if (!el) return;
    let disposed = false;
    if (window.matchMedia('(max-width: 760px)').matches) { setMode('still'); return; }
    // the scene (6 MB) only loads once the hero is near the viewport
    const io = new IntersectionObserver((entries) => {
      if (!entries.some((x) => x.isIntersecting)) return;
      io.disconnect();
      glView(el, setProgress)
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
    const next = Math.max(0, Math.min(5, n));
    setStep(next);
    view.current?.show(next, play);
  };
  const s = STEPS[step];

  return (
    <div className="story3d" ref={stage}>
      {mode === 'still' && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={STILL(step)} alt={`HOMI return station, step ${Math.max(1, step)}`} />
      )}
      {mode === 'loading' && (
        <span className="story3d-load">Loading the store… {progress ? `${Math.round(progress * 100)}%` : ''}</span>
      )}
      <div className={`story3d-card ${'tone' in s ? s.tone : ''}`}>
        <div className="story3d-head">
          <span>{step ? `${step} / 5` : '5 steps'}</span>
          <span className="story3d-dots" aria-hidden="true">
            {[1, 2, 3, 4, 5].map((i) => <i key={i} className={i <= step ? 'on' : ''} />)}
          </span>
        </div>
        <h3>{s.title}</h3>
        <p>{s.text}</p>
        <div className="story3d-nav">
          <button className="ghost" onClick={() => go(step - 1, false)} disabled={step === 0}>Back</button>
          <button onClick={() => go(step === 5 ? 0 : step + 1, step !== 5)}>
            {step === 0 ? 'Start' : step === 5 ? 'Replay' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
}

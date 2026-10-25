'use client';

// "Wrong money paid, by model" as a 3D bar grid: one row per model, one column per condition. The counts are the
// console's model table (report.ts 'model-pivot'): runs.harm summed over every run of the cell, attack and clean,
// split by condition the way studio-data.ts builds harmNoGate / harmCap / harmCounterfoil. The toggle swaps in
// runs.agentMisled, summed the same way (misledRuns). Drag to orbit, scroll to zoom; bars only move when the
// metric changes, and not at all under prefers-reduced-motion. Phones never mount this: page.tsx keeps the table.

import { useEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { CSS2DObject, CSS2DRenderer } from 'three/examples/jsm/renderers/CSS2DRenderer.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { modelName, type CounterfoilData } from './studio-data';

const CONDITIONS = ['No gate', '$200 cap', 'Counterfoil'] as const;
const METRICS = { harm: 'Wrong money paid', agentMisled: 'Agent misled' } as const;
type Metric = keyof typeof METRICS;

type Cell = {
  model: string; condition: string; runs: number; attackRuns: number;
  value: Record<Metric, number>; inAttack: Record<Metric, number>;
};

// Row order is the order models first appear in the export, as page.tsx lists them.
function cells(data: CounterfoilData) {
  const models = [...new Set(data.runs.map((r) => modelName(r.model)))];
  const grid = models.flatMap((model) =>
    CONDITIONS.map((condition): Cell => {
      const runs = data.runs.filter((r) => modelName(r.model) === model && r.condition === condition);
      const attack = runs.filter((r) => r.attackRun === 1);
      const sum = (rs: typeof runs, k: Metric) => rs.reduce((s, r) => s + Number(r[k] ?? 0), 0);
      return {
        model, condition, runs: runs.length, attackRuns: attack.length,
        value: { harm: sum(runs, 'harm'), agentMisled: sum(runs, 'agentMisled') },
        inAttack: { harm: sum(attack, 'harm'), agentMisled: sum(attack, 'agentMisled') },
      };
    }),
  );
  return { models, grid };
}

// Models run across (x), conditions front to back (z): Counterfoil in front, so its short bars hide nothing.
// The tallest bar of either metric is MAX_H, so the two metrics share one scale.
const DX = 1.25, DZ = 1.45, BAR = 0.78, MAX_H = 3.4, FLAT = 0.03;

type Hover = { cell: Cell; x: number; y: number } | null;
type Scene = { setMetric: (m: Metric) => void; dispose: () => void };

function buildScene(el: HTMLDivElement, models: string[], grid: Cell[], metric: Metric, onHover: (h: Hover) => void): Scene {
  const css = getComputedStyle(document.documentElement);
  const tone = (name: string, fallback: string) => new THREE.Color(css.getPropertyValue(name).trim() || fallback);
  const harm = tone('--cf-harm', '#d97a62'), harmDeep = tone('--cf-harm-deep', '#9a3d28');
  const green = tone('--cf-green', '#4f9a7b'), greenDeep = tone('--cf-green-deep', '#24593f');
  const border = tone('--cf-border', '#e3ddd3');

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(el.clientWidth, el.clientHeight);
  // Neutral, not the store's filmic mapping: the bars should read as the token colours.
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = 1.0;
  el.appendChild(renderer.domElement);

  const labels = new CSS2DRenderer();
  labels.setSize(el.clientWidth, el.clientHeight);
  labels.domElement.className = 'bars3d-labels';
  el.appendChild(labels.domElement);

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.6;
  scene.add(new THREE.HemisphereLight(0xfff7ee, 0xd9cfc2, 0.9));
  const sun = new THREE.DirectionalLight(0xffffff, 1.4);
  sun.position.set(6, 12, 8);
  scene.add(sun);

  const x0 = -((models.length - 1) * DX) / 2;
  const z0 = -((CONDITIONS.length - 1) * DZ) / 2;
  const width = models.length * DX, depth = CONDITIONS.length * DZ;

  // floor and hairlines between cells
  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(width + 0.6, depth + 0.6),
    new THREE.MeshStandardMaterial({ color: 0xf6f1ea, roughness: 0.95 }),
  );
  floor.rotation.x = -Math.PI / 2;
  scene.add(floor);
  const pts: number[] = [];
  for (let i = 0; i <= models.length; i++) { const x = x0 - DX / 2 + i * DX; pts.push(x, 0.002, -depth / 2, x, 0.002, depth / 2); }
  for (let j = 0; j <= CONDITIONS.length; j++) { const z = z0 - DZ / 2 + j * DZ; pts.push(-width / 2, 0.002, z, width / 2, 0.002, z); }
  const lineGeo = new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
  const lineMat = new THREE.LineBasicMaterial({ color: border });
  scene.add(new THREE.LineSegments(lineGeo, lineMat));

  const label = (text: string, cls: string, pos: THREE.Vector3, cx = 0.5, cy = 0.5) => {
    const div = document.createElement('div');
    div.className = cls;
    div.textContent = text;
    const o = new CSS2DObject(div);
    o.position.copy(pos);
    o.center.set(cx, cy);
    scene.add(o);
    return o;
  };
  models.forEach((m, i) => label(m, 'bars3d-model', new THREE.Vector3(x0 + i * DX, 0, depth / 2 + 0.3), 0.5, 0));
  CONDITIONS.forEach((c, j) => label(c, 'bars3d-cond', new THREE.Vector3(-width / 2 - 0.25, 0, z0 + j * DZ), 1, 0.5));

  // one unit box per cell, base on the floor; height is scale.y
  const box = new THREE.BoxGeometry(BAR, 1, BAR).translate(0, 0.5, 0);
  const top = Math.max(1, ...grid.flatMap((c) => [c.value.harm, c.value.agentMisled]));
  const heightOf = (c: Cell, m: Metric) => Math.max(FLAT, (c.value[m] / top) * MAX_H);
  const bars = grid.map((c) => {
    const safe = c.condition === 'Counterfoil';
    const mat = new THREE.MeshStandardMaterial({ color: safe ? green : harm, roughness: 0.8, metalness: 0 });
    const mesh = new THREE.Mesh(box, mat);
    mesh.position.set(x0 + models.indexOf(c.model) * DX, 0, z0 + CONDITIONS.indexOf(c.condition as never) * DZ);
    mesh.scale.y = heightOf(c, metric);
    mesh.userData.cell = c;
    scene.add(mesh);
    const value = label(String(c.value[metric]), 'bars3d-value', new THREE.Vector3(mesh.position.x, mesh.scale.y + 0.08, mesh.position.z), 0.5, 1);
    return { mesh, mat, value, base: mat.color.clone(), deep: safe ? greenDeep : harmDeep, cell: c };
  });

  const camera = new THREE.PerspectiveCamera(34, el.clientWidth / el.clientHeight, 0.1, 100);
  camera.position.set(1.5, 7.2, 10.8);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(0, 1.1, -0.3);
  controls.enableDamping = true;
  controls.enablePan = false;
  controls.minDistance = 6;
  controls.maxDistance = 26;
  controls.minPolarAngle = Math.PI * 0.08;
  controls.maxPolarAngle = Math.PI * 0.46;      // stay above the floor
  controls.update();

  // hover: raycast the bars, deepen the one under the pointer, hand its cell to the tooltip
  const ray = new THREE.Raycaster();
  const ndc = new THREE.Vector2();
  let hovered: (typeof bars)[number] | null = null;
  const setHovered = (b: typeof hovered) => {
    if (hovered === b) return;
    hovered?.mat.color.copy(hovered.base);
    hovered = b;
    hovered?.mat.color.copy(hovered.deep);
    renderer.domElement.style.cursor = b ? 'pointer' : '';
  };
  const onMove = (e: PointerEvent) => {
    if (e.buttons) { setHovered(null); onHover(null); return; }   // dragging the orbit
    const r = renderer.domElement.getBoundingClientRect();
    ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    const hit = ray.intersectObjects(bars.map((b) => b.mesh))[0];
    const b = hit ? bars.find((x) => x.mesh === hit.object) ?? null : null;
    setHovered(b);
    onHover(b ? { cell: b.cell, x: e.clientX - r.left, y: e.clientY - r.top } : null);
  };
  const onLeave = () => { setHovered(null); onHover(null); };
  renderer.domElement.addEventListener('pointermove', onMove);
  renderer.domElement.addEventListener('pointerleave', onLeave);

  // metric change: ease every bar from its current height to the new one, or jump under reduced motion
  const calm = window.matchMedia('(prefers-reduced-motion: reduce)');
  let anim: { from: number[]; to: number[]; t0: number } | null = null;
  const place = (b: (typeof bars)[number], h: number) => { b.mesh.scale.y = h; b.value.position.y = h + 0.08; };
  const setMetric = (m: Metric) => {
    bars.forEach((b) => { b.value.element.textContent = String(b.cell.value[m]); });
    const to = bars.map((b) => heightOf(b.cell, m));
    if (calm.matches) { bars.forEach((b, i) => place(b, to[i])); anim = null; return; }
    anim = { from: bars.map((b) => b.mesh.scale.y), to, t0: performance.now() };
  };

  let frame = 0;
  const tick = (now: number) => {
    frame = requestAnimationFrame(tick);
    if (anim) {
      const t = Math.min(1, (now - anim.t0) / 600);
      const k = 1 - Math.pow(1 - t, 3);
      bars.forEach((b, i) => place(b, anim!.from[i] + (anim!.to[i] - anim!.from[i]) * k));
      if (t === 1) anim = null;
    }
    controls.update();
    renderer.render(scene, camera);
    labels.render(scene, camera);
  };
  frame = requestAnimationFrame(tick);

  const ro = new ResizeObserver(() => {
    camera.aspect = el.clientWidth / el.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(el.clientWidth, el.clientHeight);
    labels.setSize(el.clientWidth, el.clientHeight);
  });
  ro.observe(el);

  return {
    setMetric,
    dispose() {
      cancelAnimationFrame(frame);
      ro.disconnect();
      renderer.domElement.removeEventListener('pointermove', onMove);
      renderer.domElement.removeEventListener('pointerleave', onLeave);
      controls.dispose();
      box.dispose();
      bars.forEach((b) => b.mat.dispose());
      floor.geometry.dispose();
      (floor.material as THREE.Material).dispose();
      lineGeo.dispose();
      lineMat.dispose();
      pmrem.dispose();
      renderer.dispose();
      renderer.domElement.remove();
      labels.domElement.remove();
    },
  };
}

export function ModelBars3D({ data }: { data: CounterfoilData }) {
  const mount = useRef<HTMLDivElement>(null);
  const view = useRef<Scene | null>(null);
  const { models, grid } = useMemo(() => cells(data), [data]);
  const [metric, setMetric] = useState<Metric>('harm');
  const [hover, setHover] = useState<Hover>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const el = mount.current;
    if (!el) return;
    try {
      view.current = buildScene(el, models, grid, 'harm', setHover);
    } catch (e) {
      console.warn('model bars: WebGL unavailable', e);
      setFailed(true);
    }
    return () => { view.current?.dispose(); view.current = null; };
  }, [models, grid]);

  useEffect(() => { view.current?.setMetric(metric); }, [metric]);

  const c = hover?.cell;
  return (
    <div className="bars3d">
      <div className="bars3d-bar">
        <div className="bars3d-toggle" role="group" aria-label="Metric">
          {(Object.keys(METRICS) as Metric[]).map((m) => (
            <button key={m} className={`f-patch${m === metric ? ' on' : ''}`} aria-pressed={m === metric} onClick={() => setMetric(m)}>
              {/* Codex's felt buttons (docs/gorseller/site-tasarim/chart-buttons-v1/), plum when chosen */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={`buttons/metric-${m}${m === metric ? '-on' : ''}.webp`} alt={METRICS[m]} />
            </button>
          ))}
        </div>
        <div className="bars3d-legend">
          <span><i className="harm" />No gate, $200 cap</span>
          <span><i className="green" />Counterfoil</span>
        </div>
      </div>
      <div className="bars3d-stage" ref={mount}>
        {failed && <span className="bars3d-note">3D is not available in this browser; the same numbers are in the table above.</span>}
        {!failed && <span className="bars3d-hint">Drag to orbit · scroll to zoom · hover a bar</span>}
        {c && (
          <div className="bars3d-tip" style={{ left: hover.x, top: hover.y }}>
            <b>{c.model}</b>
            <small>{c.condition}</small>
            <strong>
              {c.value[metric]}
              <span> of {c.runs} runs</span>
            </strong>
            <em>
              {METRICS[metric].toLowerCase()} · {c.inAttack[metric]} in {c.attackRuns} attack runs, {c.value[metric] - c.inAttack[metric]} in{' '}
              {c.runs - c.attackRuns} clean runs
            </em>
          </div>
        )}
      </div>
    </div>
  );
}

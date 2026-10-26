'use client';

// Counterfoil in 3D for the Overview hero: the felt figure from docs/gorseller/karakterler/counterfoil-claude-3d.blend
// (tools/counterfoil_claude_3d.py), exported as public/3d/counterfoil-claude.glb. His upper half ('CF_Upper': body,
// beret, brows, moustache, arms) turns towards the pointer and his bead eyes ('CF_Eyes', a pivot inside the egg) roll a
// little further, both clamped and eased. Feet stay planted. With reduced motion he stands still; phones and touch
// screens get the flat felt render instead (no 3D on phones).

import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { FollowingFoil } from './felt';

const MODEL = '3d/counterfoil-claude.glb?v=20261026';
const BODY = { yaw: 0.5, up: 0.12, down: 0.2 };      // radians the upper half may turn / nod
const EYES = { yaw: 0.22, up: 0.1, down: 0.12 };     // extra roll of the bead eyes on top of that
const DEPTH = 650;                                   // px: how far in front of the screen he imagines the pointer

// Needle felt without textures (the GLB has no UVs): a fine 3D noise in the model's own space breaks up the normal
// and the colour, and sheen gives the soft fuzzy rim. Beads stay glossy.
function feltify(src: THREE.MeshStandardMaterial): THREE.Material {
  if (src.name.startsWith('Bead')) {
    return new THREE.MeshPhysicalMaterial({ color: src.color, roughness: 0.08, clearcoat: 1, clearcoatRoughness: 0.05 });
  }
  const m = new THREE.MeshPhysicalMaterial({
    color: src.color, roughness: 0.92, sheen: 0.6, sheenRoughness: 0.55,
    sheenColor: new THREE.Color(src.color).lerp(new THREE.Color(0xffffff), 0.2),
  });
  m.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vFeltPos;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvFeltPos = position;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>
varying vec3 vFeltPos;
float fh(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }
float fn(vec3 p) {
  vec3 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(fh(i), fh(i + vec3(1,0,0)), f.x), mix(fh(i + vec3(0,1,0)), fh(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(fh(i + vec3(0,0,1)), fh(i + vec3(1,0,1)), f.x), mix(fh(i + vec3(0,1,1)), fh(i + vec3(1,1,1)), f.x), f.y), f.z);
}
float felt(vec3 p) { return fn(p * 140.0) * 0.55 + fn(p * 320.0 + 7.0) * 0.3 + fn(p * 38.0 + 3.0) * 0.15; }`)
      .replace('#include <color_fragment>', '#include <color_fragment>\ndiffuseColor.rgb *= 0.9 + 0.16 * felt(vFeltPos);')
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
{
  vec3 q = vFeltPos;
  vec3 g = vec3(felt(q + vec3(0.002, 0, 0)), felt(q + vec3(0, 0.002, 0)), felt(q + vec3(0, 0, 0.002))) - felt(q);
  normal = normalize(normal - mat3(viewMatrix) * g * 7.0);
}`);
  };
  return m;
}

export function Counterfoil3D() {
  const mount = useRef<HTMLDivElement>(null);
  const [mode, setMode] = useState<'3d' | 'flat'>('3d');

  useEffect(() => {
    const el = mount.current;
    if (!el) return;
    if (window.matchMedia('(max-width: 760px), (hover: none), (pointer: coarse)').matches) { setMode('flat'); return; }
    const calm = window.matchMedia('(prefers-reduced-motion: reduce)');

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(el.clientWidth, el.clientHeight);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 0.92;
    el.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const pmrem = new THREE.PMREMGenerator(renderer);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environmentIntensity = 0.55;
    scene.add(new THREE.HemisphereLight(0xfff4e6, 0xcdb9a5, 0.7));
    const key = new THREE.DirectionalLight(0xfff1e0, 2.2);
    key.position.set(-2.5, 3.5, 4);
    scene.add(key);
    const rim = new THREE.DirectionalLight(0xffffff, 1.1);
    rim.position.set(3, 2.5, -3);
    scene.add(rim);

    // a soft contact shadow under the slippers
    const sc = document.createElement('canvas');
    sc.width = sc.height = 128;
    const g = sc.getContext('2d')!;
    const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    grad.addColorStop(0, 'rgba(70,48,20,.35)');
    grad.addColorStop(1, 'rgba(70,48,20,0)');
    g.fillStyle = grad;
    g.fillRect(0, 0, 128, 128);
    const shadowTex = new THREE.CanvasTexture(sc);
    const shadow = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 0.8), new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false }));
    shadow.rotation.x = -Math.PI / 2;
    shadow.position.set(0, 0.002, 0.05);
    scene.add(shadow);

    const camera = new THREE.PerspectiveCamera(24, el.clientWidth / el.clientHeight, 0.1, 50);
    camera.position.set(0.35, 1.05, 5.4);
    camera.lookAt(0, 0.86, 0);

    let upper: THREE.Object3D | undefined, eyes: THREE.Object3D | undefined;
    const rest = { upper: new THREE.Euler(), eyes: new THREE.Euler() };
    const aim = { yaw: 0, pitch: 0 }, now = { yaw: 0, pitch: 0 };

    const draco = new DRACOLoader().setDecoderPath('draco/');
    const loader = new GLTFLoader().setDRACOLoader(draco);
    let disposed = false;
    loader.load(MODEL, (gltf) => {
      if (disposed) return;
      gltf.scene.traverse((o) => {
        const mesh = o as THREE.Mesh;
        if (!mesh.isMesh) return;
        const old = mesh.material as THREE.MeshStandardMaterial;
        mesh.material = feltify(old);
        old.dispose();
      });
      upper = gltf.scene.getObjectByName('CF_Upper');
      eyes = gltf.scene.getObjectByName('CF_Eyes');
      if (upper) rest.upper.copy(upper.rotation);
      if (eyes) rest.eyes.copy(eyes.rotation);
      scene.add(gltf.scene);
      kick();
    });

    // pointer -> where he should look: an angle towards a point DEPTH px in front of the screen
    const onMove = (e: PointerEvent) => {
      if (calm.matches) return;
      const r = el.getBoundingClientRect();
      aim.yaw = Math.atan2(e.clientX - (r.left + r.width / 2), DEPTH);
      aim.pitch = Math.atan2(e.clientY - (r.top + r.height * 0.42), DEPTH);
      kick();
    };
    const onLeave = () => { aim.yaw = 0; aim.pitch = 0; kick(); };
    window.addEventListener('pointermove', onMove);
    document.addEventListener('pointerleave', onLeave);

    const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));
    let raf = 0, last = 0, visible = true;
    function kick() { if (!raf && visible) { last = performance.now(); raf = requestAnimationFrame(frame); } }
    function frame(t: number) {
      raf = 0;
      const k = 1 - Math.exp(-(t - last) / 1000 * 6);    // eased follow, frame-rate independent
      last = t;
      now.yaw += (aim.yaw - now.yaw) * k;
      now.pitch += (aim.pitch - now.pitch) * k;
      // the body takes the first part of the turn, the eyes the rest; up on screen is a turn about -X
      const by = clamp(now.yaw, -BODY.yaw, BODY.yaw), bp = clamp(now.pitch, -BODY.up, BODY.down);
      const ey = clamp(now.yaw - by, -EYES.yaw, EYES.yaw), ep = clamp(now.pitch * 0.6, -EYES.up, EYES.down);
      if (upper) upper.rotation.set(rest.upper.x + bp, rest.upper.y + by, rest.upper.z - by * 0.08);
      if (eyes) eyes.rotation.set(rest.eyes.x + ep, rest.eyes.y + ey, rest.eyes.z);
      renderer.render(scene, camera);
      if (Math.abs(aim.yaw - now.yaw) + Math.abs(aim.pitch - now.pitch) > 0.0005) kick();
    }

    const seen = new IntersectionObserver(([en]) => { visible = en.isIntersecting; kick(); });
    seen.observe(el);
    const resize = () => {
      camera.aspect = el.clientWidth / el.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(el.clientWidth, el.clientHeight);
      kick();
    };
    window.addEventListener('resize', resize);

    return () => {
      disposed = true;
      cancelAnimationFrame(raf);
      seen.disconnect();
      window.removeEventListener('pointermove', onMove);
      document.removeEventListener('pointerleave', onLeave);
      window.removeEventListener('resize', resize);
      draco.dispose();
      shadowTex.dispose();
      pmrem.dispose();
      renderer.dispose();
      el.removeChild(renderer.domElement);
    };
  }, []);

  if (mode === 'flat') return <FollowingFoil src="crew/counterfoil.webp" alt="Counterfoil, HOMI's felt gatekeeper" />;
  return <div className="foil3d" ref={mount} role="img" aria-label="Counterfoil, HOMI's felt gatekeeper, in 3D; he looks towards your pointer" />;
}

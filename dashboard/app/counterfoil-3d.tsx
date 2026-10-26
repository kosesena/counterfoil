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

const MODEL = '3d/counterfoil-claude.glb?v=20261026h';
const BODY = { yaw: 0.5, up: 0.12, down: 0.2 };      // radians the upper half may turn / nod
const EYES = { yaw: 0.22, up: 0.1, down: 0.03 };     // extra roll of the bead eyes on top of that (barely down: the moustache is right below)
const DEPTH = 650;                                   // px: how far in front of the screen he imagines the pointer

// Needle felt: a tile of curly wool fibres drawn once on a canvas, laid over every part triplanar (the GLB has no UVs,
// so the tile is projected along the three axes of the part's own space and blended by the surface normal). It lightens
// and darkens the colour fibre by fibre and bumps the surface along them. Wool is matte: no sheen, no specular, only a
// little diffuse light from the room. The beads keep a soft gloss.
let fibreTile: THREE.CanvasTexture | null = null;
function fibres(): THREE.CanvasTexture {
  if (fibreTile) return fibreTile;
  const N = 512, c = document.createElement('canvas');
  c.width = c.height = N;
  const g = c.getContext('2d')!;
  g.fillStyle = '#808080';
  g.fillRect(0, 0, N, N);
  let seed = 7;
  const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  g.lineCap = 'round';
  for (let i = 0; i < 1500; i++) {
    // one fibre: a short curling stroke, light or dark, drawn nine times so the tile wraps without a seam
    const pts: [number, number][] = [];
    let x = rnd() * N, y = rnd() * N, a = rnd() * Math.PI * 2;
    const curl = (rnd() - 0.5) * 0.5, steps = 8 + Math.floor(rnd() * 22);
    for (let k = 0; k < steps; k++) {
      pts.push([x, y]);
      a += curl + (rnd() - 0.5) * 0.35;
      x += Math.cos(a) * 4.5;
      y += Math.sin(a) * 4.5;
    }
    const light = rnd() < 0.55;
    g.strokeStyle = light ? `rgba(255,255,255,${0.16 + rnd() * 0.2})` : `rgba(0,0,0,${0.14 + rnd() * 0.18})`;
    g.lineWidth = 1.6 + rnd() * 2.2;
    for (const ox of [-N, 0, N]) for (const oy of [-N, 0, N]) {
      g.beginPath();
      pts.forEach(([px, py], k) => (k ? g.lineTo(px + ox, py + oy) : g.moveTo(px + ox, py + oy)));
      g.stroke();
    }
  }
  fibreTile = new THREE.CanvasTexture(c);
  fibreTile.wrapS = fibreTile.wrapT = THREE.RepeatWrapping;
  fibreTile.colorSpace = THREE.NoColorSpace;
  fibreTile.anisotropy = 4;
  return fibreTile;
}

function feltify(src: THREE.MeshStandardMaterial): THREE.Material {
  if (src.name.startsWith('Bead')) {
    return new THREE.MeshPhysicalMaterial({ color: src.color, roughness: 0.08, clearcoat: 0.4, clearcoatRoughness: 0.2, envMapIntensity: 1.2 });
  }
  const m = new THREE.MeshPhysicalMaterial({
    color: src.color, roughness: 1, specularIntensity: 0, envMapIntensity: 0.35,
  });
  m.onBeforeCompile = (sh) => {
    sh.uniforms.feltMap = { value: fibres() };
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vFeltPos;\nvarying vec3 vFeltN;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvFeltPos = position;\nvFeltN = normal;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>
uniform sampler2D feltMap;
varying vec3 vFeltPos;
varying vec3 vFeltN;
float feltH;
float tri(vec3 p, vec3 w, float s) {
  return texture2D(feltMap, p.yz * s).r * w.x + texture2D(feltMap, p.xz * s + 0.37).r * w.y + texture2D(feltMap, p.xy * s + 0.71).r * w.z;
}`)
      .replace('#include <color_fragment>', `#include <color_fragment>
{
  vec3 w = pow(abs(normalize(vFeltN)), vec3(4.0));
  w /= w.x + w.y + w.z;
  feltH = tri(vFeltPos, w, 2.3) * 0.7 + tri(vFeltPos * 0.55 + 0.13, w, 2.3) * 0.3;
  diffuseColor.rgb *= 1.0 + (feltH - 0.5) * 1.0;
}`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
{
  vec3 sx = dFdx(-vViewPosition), sy = dFdy(-vViewPosition);
  vec3 r1 = cross(sy, normal), r2 = cross(normal, sx);
  float det = dot(sx, r1);
  vec2 dh = vec2(dFdx(feltH), dFdy(feltH)) * 0.04;
  normal = normalize(abs(det) * normal - sign(det) * (dh.x * r1 + dh.y * r2));
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
    renderer.toneMappingExposure = 1.0;
    el.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const pmrem = new THREE.PMREMGenerator(renderer);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environmentIntensity = 0.3;
    scene.add(new THREE.HemisphereLight(0xfff4e6, 0x8f7a6a, 0.45));
    const key = new THREE.DirectionalLight(0xfff1e0, 3.0);
    key.position.set(-4, 3.2, 2.6);
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
    camera.position.set(0.3, 1.6, 5.4);
    camera.lookAt(0, 0.74, 0);

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

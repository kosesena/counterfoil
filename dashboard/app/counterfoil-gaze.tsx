'use client';

// Same body/eye pivot approach as the Claude hero, applied to our own Blender model.
// The black beads move as whole objects; there are no added irises or pupil overlays.
import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import styles from './counterfoil-gaze.module.css';

export function CounterfoilGaze() {
  const root = useRef<HTMLDivElement>(null);
  const [loaded, setLoaded] = useState(false);
  useEffect(() => {
    const el = root.current;
    if (!el) return;
    const fine = matchMedia('(hover: hover) and (pointer: fine)');
    const reduced = matchMedia('(prefers-reduced-motion: reduce)');
    if (!fine.matches) return;
    let renderer: THREE.WebGLRenderer;
    try { renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true }); }
    catch { return; }
    renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = .95;
    renderer.domElement.setAttribute('aria-hidden', 'true');
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const pmrem = new THREE.PMREMGenerator(renderer);
    const room = new RoomEnvironment();
    const environment = pmrem.fromScene(room, .04);
    room.dispose(); pmrem.dispose();
    scene.environment = environment.texture;
    scene.environmentIntensity = .35;
    scene.add(new THREE.HemisphereLight(0xfff3e5, 0x58404c, .45));
    const key = new THREE.DirectionalLight(0xfff1df, 2.4);
    key.position.set(-4, 7, 5); scene.add(key);
    const fill = new THREE.DirectionalLight(0xffffff, .45);
    fill.position.set(4, 4, 2); scene.add(fill);
    const rim = new THREE.DirectionalLight(0xffe7d0, .9);
    rim.position.set(2, 6, -3); scene.add(rim);
    const camera = new THREE.OrthographicCamera(-2, 2, 2.825, -2.825, .1, 100);
    camera.position.set(-1.4, 4.2, 12); camera.lookAt(0, 2.43, .02);
    const draco = new DRACOLoader().setDecoderPath('draco/');
    let upper: THREE.Object3D | undefined, eyes: THREE.Object3D | undefined, model: THREE.Group | undefined;
    let disposed = false, visible = true, frameId = 0, previous = 0;
    const aim = { yaw: 0, pitch: 0 }, current = { yaw: 0, pitch: 0 };
    let pointer: { x: number; y: number } | null = null;
    const clamp = THREE.MathUtils.clamp;
    const render = (now: number) => {
      frameId = 0;
      const dt = Math.min(64, previous ? now - previous : 16); previous = now;
      const ease = 1 - Math.exp(-dt / 130);
      current.yaw += (aim.yaw - current.yaw) * ease;
      current.pitch += (aim.pitch - current.pitch) * ease;
      const yaw = clamp(current.yaw, -.30, .30), pitch = clamp(current.pitch, -.065, .10);
      if (upper) upper.rotation.set(pitch, yaw, -yaw * .045);
      if (eyes) eyes.rotation.set(clamp(current.pitch * .25, -.065, .018), clamp(current.yaw * .3, -.12, .12), 0);
      renderer.render(scene, camera);
      // Observable pose also makes pointer-regression checks independent of screenshots.
      el.dataset.gazeYaw = yaw.toFixed(4); el.dataset.gazePitch = pitch.toFixed(4);
      if (Math.abs(aim.yaw-current.yaw)+Math.abs(aim.pitch-current.pitch)>.0005) kick();
      else previous = 0;
    };
    function kick() { if (!frameId && !disposed && visible) frameId = requestAnimationFrame(render); }
    const updateAim = () => {
      const r = el.getBoundingClientRect();
      aim.yaw = pointer ? clamp(Math.atan2(pointer.x-r.left-r.width*.53, 650), -.65, .65) : 0;
      aim.pitch = pointer ? clamp(Math.atan2(pointer.y-r.top-r.height*.36, 650), -.4, .4) : 0;
      kick();
    };
    const onMove = (event: PointerEvent) => {
      if (!fine.matches || reduced.matches || event.pointerType==='touch' || !visible) return;
      pointer = { x: event.clientX, y: event.clientY }; updateAim();
    };
    const reset = () => { pointer = null; updateAim(); };
    const calm = () => {
      pointer=null; aim.yaw=aim.pitch=current.yaw=current.pitch=0; kick();
    };
    const onVisibility = () => {
      if (document.hidden) { cancelAnimationFrame(frameId); frameId=0; previous=0; }
      else reset();
    };
    const disposeModel = (object: THREE.Object3D) => {
      object.traverse(child => {
        const mesh=child as THREE.Mesh;
        if (!mesh.isMesh) return;
        mesh.geometry.dispose();
        (Array.isArray(mesh.material) ? mesh.material : [mesh.material]).forEach(m=>m.dispose());
      });
    };
    new GLTFLoader().setDRACOLoader(draco).load('3d/counterfoil-codex.glb', gltf => {
      if (disposed) { disposeModel(gltf.scene); return; }
      model=gltf.scene; upper=model.getObjectByName('CF_Upper'); eyes=model.getObjectByName('CF_Eyes');
      model.traverse(child => {
        const mesh=child as THREE.Mesh;
        if (!mesh.isMesh) return;
        const mat=mesh.material as THREE.MeshStandardMaterial;
        if (mesh.name.startsWith('CF_eyes')) {
          mat.envMapIntensity=1.5; mat.roughness=.12;
        } else {
          // sRGB swatches matched to the reference; matte wool must not wash out like plastic.
          const swatches: Record<string, string> = {
            '01': '#5a2047', '02': '#77335c',
            '03': '#9b2315', '04': '#bc3820',
            '05': '#f4cd92', '06': '#ffe3ad',
            '07': '#c88bc5', '08': '#e7b5df',
          };
          const id=mat.name.match(/WEB (\d{2})/)?.[1];
          const wool=new THREE.MeshPhysicalMaterial({
            color: id && swatches[id] ? swatches[id] : mat.color,
            roughness: 1, specularIntensity: .12, envMapIntensity: .25,
          });
          if (id === '05' || id === '06') {
            wool.emissive.set('#ffd6a0'); wool.emissiveIntensity=.14;
          }
          mesh.material=wool; mat.dispose();
        }
      });
      scene.add(model); setLoaded(true); kick();
    }, undefined, () => { if (!disposed) { setLoaded(false); renderer.domElement.style.visibility='hidden'; } });
    const resize = () => {
      const width=el.clientWidth, height=el.clientHeight;
      if (!width || !height) return;
      camera.left=-2.825*width/height; camera.right=2.825*width/height; camera.updateProjectionMatrix();
      renderer.setSize(width,height); updateAim();
    };
    const sizeObserver=new ResizeObserver(resize); sizeObserver.observe(el); resize();
    const seen=new IntersectionObserver(([entry]) => { visible=entry.isIntersecting; if (!visible) { cancelAnimationFrame(frameId); frameId=0; } else reset(); });
    seen.observe(el);
    window.addEventListener('pointermove',onMove,{passive:true});
    document.documentElement.addEventListener('pointerleave',reset);
    window.addEventListener('blur',reset); window.addEventListener('scroll',updateAim,{passive:true});
    document.addEventListener('visibilitychange',onVisibility);
    fine.addEventListener('change',calm); reduced.addEventListener('change',calm);
    const contextLost = (event: Event) => { event.preventDefault(); setLoaded(false); };
    renderer.domElement.addEventListener('webglcontextlost',contextLost);
    return () => {
      disposed=true; cancelAnimationFrame(frameId); seen.disconnect(); sizeObserver.disconnect();
      window.removeEventListener('pointermove',onMove); window.removeEventListener('blur',reset); window.removeEventListener('scroll',updateAim);
      document.documentElement.removeEventListener('pointerleave',reset); document.removeEventListener('visibilitychange',onVisibility);
      fine.removeEventListener('change',calm); reduced.removeEventListener('change',calm);
      renderer.domElement.removeEventListener('webglcontextlost',contextLost);
      if (model) disposeModel(model);
      draco.dispose(); environment.dispose(); renderer.dispose(); renderer.domElement.remove();
    };
  }, []);

  return <div className={`foil ${styles.character}`} ref={root} data-model-loaded={loaded}
    role="img" aria-label="Counterfoil, the wool gatekeeper; his black bead eyes and body follow your pointer">
    {/* eslint-disable-next-line @next/next/no-img-element */}
    <img src="crew/counterfoil-codex.webp" width={1100} height={1500} alt="" draggable={false}
      className={loaded ? styles.hidden : undefined} />
  </div>;
}

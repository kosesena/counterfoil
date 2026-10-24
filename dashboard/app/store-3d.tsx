'use client';

// The HOMI self-service return station from the Blender store (docs/gorseller/counterfoil-magaza.blend),
// exported as public/3d/homi-return-station.glb by tools/export_station_glb.py. Drag to orbit, scroll
// to zoom. Nothing moves on its own. Phones get the still render instead of a WebGL scene.

import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';

// Blender (x, y, z) is glTF (x, z, -y). Station centre and the hero camera from the .blend.
const TARGET = new THREE.Vector3(-13.5, 0.9, 8.7);
const CAMERA = new THREE.Vector3(-9.4, 2.6, 4.4);

export function Store3D() {
  const mount = useRef<HTMLDivElement>(null);
  const [state, setState] = useState<'loading' | 'ready' | 'error' | 'still'>('loading');

  useEffect(() => {
    const el = mount.current;
    if (!el) return;
    if (window.matchMedia('(max-width: 760px)').matches) {
      setState('still');
      return;
    }

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(el.clientWidth, el.clientHeight);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 0.88;
    el.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const pmrem = new THREE.PMREMGenerator(renderer);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.add(new THREE.HemisphereLight(0xfff7ee, 0xd9cfc2, 0.45));
    const sun = new THREE.DirectionalLight(0xffffff, 1.1);
    sun.position.set(-6, 12, 14);
    scene.add(sun);

    const floor = new THREE.Mesh(
      new THREE.CircleGeometry(14, 64),
      new THREE.MeshStandardMaterial({ color: 0xe9e3da, roughness: 0.9 }),
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.set(TARGET.x, 0, TARGET.z);
    scene.add(floor);

    const camera = new THREE.PerspectiveCamera(38, el.clientWidth / el.clientHeight, 0.1, 200);
    camera.position.copy(CAMERA);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.copy(TARGET);
    controls.enableDamping = true;
    controls.minDistance = 2.5;
    controls.maxDistance = 14;
    controls.maxPolarAngle = Math.PI * 0.48;      // stay above the floor
    controls.enablePan = false;
    controls.update();

    const draco = new DRACOLoader().setDecoderPath('draco/');
    const loader = new GLTFLoader().setDRACOLoader(draco);
    let disposed = false;
    loader.load(
      '3d/homi-return-station.glb',
      (gltf) => {
        if (disposed) return;
        scene.add(gltf.scene);
        setState('ready');
      },
      undefined,
      () => setState('error'),
    );

    let frame = 0;
    const tick = () => {
      frame = requestAnimationFrame(tick);
      controls.update();
      renderer.render(scene, camera);
    };
    tick();

    const resize = () => {
      camera.aspect = el.clientWidth / el.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(el.clientWidth, el.clientHeight);
    };
    window.addEventListener('resize', resize);

    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      window.removeEventListener('resize', resize);
      controls.dispose();
      draco.dispose();
      pmrem.dispose();
      renderer.dispose();
      el.removeChild(renderer.domElement);
    };
  }, []);

  return (
    <div className="store3d" ref={mount}>
      {state === 'still' && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src="3d/homi-return-station.png" alt="HOMI self-service return station" />
      )}
      {state === 'loading' && <span className="store3d-note">Loading the store…</span>}
      {state === 'error' && <span className="store3d-note">The 3D store could not be loaded.</span>}
      {state === 'ready' && <span className="store3d-hint">Drag to look around · scroll to zoom</span>}
    </div>
  );
}

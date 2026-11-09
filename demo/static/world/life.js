// Small signs of life in the HOMI store: the cast breathes and sways, shoppers cross the floor, plants and a display
// fill the room. Runs only while the canvas is on screen; visitors who ask for reduced motion get a still store.
import * as THREE from "three";

const felt = (color) => new THREE.MeshStandardMaterial({ color, roughness: 1, metalness: 0 });
const DARK = felt("#241b18");

function part(geo, mat, x, y, z, parent) { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = false; parent.add(m); return m; }

function shopper({ coat, skin, hat, bag }) {
  const g = new THREE.Group(), body = new THREE.Group(); g.add(body);
  const legGeo = new THREE.CapsuleGeometry(0.075, 0.22, 4, 10), armGeo = new THREE.CapsuleGeometry(0.06, 0.32, 4, 10);
  const legs = [part(legGeo, felt("#3b3a48"), -0.12, 0.2, 0, g), part(legGeo, felt("#3b3a48"), 0.12, 0.2, 0, g)];
  part(new THREE.CapsuleGeometry(0.27, 0.42, 6, 16), felt(coat), 0, 0.72, 0, body);
  const arms = [part(armGeo, felt(coat), -0.33, 0.78, 0, body), part(armGeo, felt(coat), 0.33, 0.78, 0, body)];
  part(new THREE.SphereGeometry(0.25, 20, 16), felt(skin), 0, 1.32, 0, body);
  part(new THREE.SphereGeometry(0.262, 20, 12, 0, Math.PI * 2, 0, Math.PI * 0.46), felt(hat), 0, 1.36, 0, body);
  for (const x of [-0.09, 0.09]) part(new THREE.SphereGeometry(0.034, 10, 8), DARK, x, 1.33, 0.235, body);
  if (bag) { const b = part(new THREE.BoxGeometry(0.3, 0.26, 0.14), felt(bag), 0.42, 0.42, 0.02, body); b.rotation.z = 0.05; }
  const blob = new THREE.Mesh(new THREE.CircleGeometry(0.42, 24), new THREE.MeshBasicMaterial({ color: "#3a2415", transparent: true, opacity: 0.2, depthWrite: false }));
  blob.rotation.x = -Math.PI / 2; blob.position.y = 0.03; g.add(blob);
  return { g, body, legs, arms };
}

function topiary(scene, x, z) {
  const g = new THREE.Group(); g.position.set(x, 0, z);
  part(new THREE.CylinderGeometry(0.34, 0.25, 0.52, 20), felt("#b5623c"), 0, 0.26, 0, g);
  part(new THREE.CylinderGeometry(0.03, 0.03, 0.9, 8), felt("#6d4a31"), 0, 0.85, 0, g);
  [[0, 0.82, 0.36], [0.03, 1.28, 0.42], [-0.02, 1.76, 0.3]].forEach(([dx, y, r], i) => part(new THREE.SphereGeometry(r, 20, 16), felt(i % 2 ? "#5d8c62" : "#4c7a56"), dx, y, 0, g));
  scene.add(g);
}

function display(scene, x, z) {
  const g = new THREE.Group(); g.position.set(x, 0, z);
  part(new THREE.BoxGeometry(1.5, 0.08, 0.8), felt("#8a5a38"), 0, 0.72, 0, g);
  for (const [dx, dz] of [[-0.66, -0.32], [0.66, -0.32], [-0.66, 0.32], [0.66, 0.32]]) part(new THREE.CylinderGeometry(0.04, 0.04, 0.72, 8), felt("#6d4a31"), dx, 0.36, dz, g);
  [["#d9583b", -0.48, 0], ["#f0c56b", -0.1, 0.1], ["#3f7f8c", 0.3, -0.08], ["#efe6d6", 0.56, 0.14]].forEach(([c, dx, dz], i) => { const h = 0.2 + (i % 2) * 0.1; part(new THREE.BoxGeometry(0.3, h, 0.3), felt(c), dx, 0.76 + h / 2, dz, g); });
  scene.add(g);
}

const ROUTES = [
  { from: [-20, 16.3], to: [-1, 16.3], s: 0.9, look: { coat: "#c9583f", skin: "#f0c7a4", hat: "#5a3a29", bag: "#efe6d6" } },
  { from: [-1.5, 15.2], to: [-20, 15.2], s: 0.72, look: { coat: "#3d7180", skin: "#c98f62", hat: "#e7b53f" } },
  { from: [-19, 2.4], to: [-3, 2.4], s: 0.8, look: { coat: "#7c5aa0", skin: "#f3d2b4", hat: "#2c2733", bag: "#d9a441" } },
];

export function startLife({ scene, renderer, actors, draw, calm }) {
  topiary(scene, -17.2, 14.2); topiary(scene, -4.2, 14.4); display(scene, -5.9, 14.9);
  const walkers = ROUTES.map((r) => { const s = shopper(r.look); scene.add(s.g); return { ...r, ...s, u: Math.random() }; });
  const place = (w, phase) => {
    const len = Math.hypot(w.to[0] - w.from[0], w.to[1] - w.from[1]), u = (w.u + phase * w.s / len) % 1, tri = u < 0.5 ? u * 2 : 2 - u * 2;
    w.g.position.set(w.from[0] + (w.to[0] - w.from[0]) * tri, 0, w.from[1] + (w.to[1] - w.from[1]) * tri);
    const dir = (u < 0.5 ? 1 : -1) * Math.sign(w.to[0] - w.from[0]); w.g.rotation.y = dir > 0 ? Math.PI / 2 : -Math.PI / 2;
    const swing = Math.sin(phase * 6.5 + w.u * 9);
    w.legs[0].rotation.x = swing * 0.45; w.legs[1].rotation.x = -swing * 0.45; w.arms[0].rotation.x = -swing * 0.3; w.arms[1].rotation.x = swing * 0.3;
    w.body.position.y = Math.abs(swing) * 0.035;
  };
  walkers.forEach((w) => place(w, 0));
  const keys = Object.keys(actors).filter((k) => actors[k].pivot);
  const last = {};
  renderer.shadowMap.autoUpdate = false; renderer.shadowMap.needsUpdate = true;
  if (calm || matchMedia("(prefers-reduced-motion: reduce)").matches) { draw(); return; }
  let visible = true, prev = 0;
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; }).observe(renderer.domElement);
  function frame(now) {
    requestAnimationFrame(frame);
    if (!visible || document.hidden || now - prev < 33) return;
    prev = now;
    const t = now / 1000;
    keys.forEach((k, i) => {
      const a = actors[k], p = a.pivot, b = 1 + Math.sin(t * 1.7 + i * 1.3) * 0.012;
      p.scale.set(2 - b, b, 2 - b); p.rotation.z = Math.sin(t * 0.8 + i * 2.1) * 0.018;
      const was = last[k];
      if (!was || was.distanceToSquared(p.position) > 1e-5) { renderer.shadowMap.needsUpdate = true; last[k] = p.position.clone(); }
    });
    walkers.forEach((w) => place(w, t));
    draw();
  }
  requestAnimationFrame(frame);
}

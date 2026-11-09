// Warms up the HOMI store at load time: a scanned oak floor, warm light with soft shadows, and strings of bulbs.
// The felt cast and the store's geometry stay as exported. Floor texture: Laminate Floor 02, Poly Haven (CC0).
import * as THREE from "three";

const FLOOR_MATERIALS = /FELT \| ivory/;
const TILE = 2.4; // world units per texture repeat

function takeFloor(root) {
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3(), n = new THREE.Vector3();
  const out = [];
  root.updateMatrixWorld(true);
  root.traverse((m) => {
    if (!m.isMesh || !FLOOR_MATERIALS.test(m.material.name || "") || !m.geometry.index) return;
    const pos = m.geometry.attributes.position, idx = m.geometry.index.array, kept = [];
    for (let i = 0; i < idx.length; i += 3) {
      a.fromBufferAttribute(pos, idx[i]).applyMatrix4(m.matrixWorld);
      b.fromBufferAttribute(pos, idx[i + 1]).applyMatrix4(m.matrixWorld);
      c.fromBufferAttribute(pos, idx[i + 2]).applyMatrix4(m.matrixWorld);
      n.copy(b).sub(a).cross(c.clone().sub(a)).normalize();
      if (n.y > 0.98 && Math.max(Math.abs(a.y), Math.abs(b.y), Math.abs(c.y)) < 0.08) out.push(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z);
      else kept.push(idx[i], idx[i + 1], idx[i + 2]);
    }
    m.geometry.setIndex(kept);
  });
  return out;
}

function floorMesh(tris, redraw) {
  const g = new THREE.BufferGeometry(), count = tris.length / 3;
  const uv = new Float32Array(count * 2), normal = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) { uv[i * 2] = tris[i * 3] / TILE; uv[i * 2 + 1] = tris[i * 3 + 2] / TILE; normal[i * 3 + 1] = 1; }
  g.setAttribute("position", new THREE.Float32BufferAttribute(tris, 3));
  g.setAttribute("normal", new THREE.BufferAttribute(normal, 3));
  g.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
  const load = new THREE.TextureLoader(), tex = (url, srgb) => { const t = load.load(url, () => redraw?.()); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 8; if (srgb) t.colorSpace = THREE.SRGBColorSpace; return t; };
  const mat = new THREE.MeshStandardMaterial({ map: tex("/static/world/floor-oak.jpg", true), normalMap: tex("/static/world/floor-oak-nor.jpg", false), roughness: 0.42, metalness: 0 });
  mat.normalScale.set(0.5, 0.5);
  const mesh = new THREE.Mesh(g, mat); mesh.name = "HOMI_OakFloor"; mesh.receiveShadow = true;
  return mesh;
}

function glowTexture() {
  const c = document.createElement("canvas"); c.width = c.height = 64;
  const x = c.getContext("2d"), g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
  g.addColorStop(0, "rgba(255,226,170,1)"); g.addColorStop(0.3, "rgba(255,190,110,.42)"); g.addColorStop(1, "rgba(255,170,90,0)");
  x.fillStyle = g; x.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

// [from, to, bulbs, sag], world coordinates around the checkout area
const STRANDS = [
  [[-19, 4.3, 3.2], [-13, 4.3, 3.2], 13, 0.55], [[-13, 4.3, 3.2], [-7, 4.3, 3.2], 13, 0.55], [[-7, 4.3, 3.2], [-1, 4.3, 3.2], 13, 0.55],
  [[-19, 3.5, 7.4], [-13, 3.5, 7.4], 13, 0.45], [[-13, 3.5, 7.4], [-7, 3.5, 7.4], 13, 0.45], [[-7, 3.5, 7.4], [-1, 3.5, 7.4], 13, 0.45],
];

function bulbs(scene) {
  const pts = [], line = [];
  const at = (a, b, sag, u) => new THREE.Vector3(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u - sag * 4 * u * (1 - u), a[2] + (b[2] - a[2]) * u);
  for (const [a, b, n, sag] of STRANDS) {
    for (let i = 0; i < 24; i++) { const p = at(a, b, sag, i / 24), q = at(a, b, sag, (i + 1) / 24); line.push(p.x, p.y, p.z, q.x, q.y, q.z); }
    for (let i = 0; i < n; i++) { const p = at(a, b, sag, (i + 0.5) / n); p.y -= 0.09; pts.push(p); }
  }
  const wire = new THREE.BufferGeometry(); wire.setAttribute("position", new THREE.Float32BufferAttribute(line, 3));
  scene.add(new THREE.LineSegments(wire, new THREE.LineBasicMaterial({ color: "#3a2a20" })));
  const mesh = new THREE.InstancedMesh(new THREE.SphereGeometry(0.07, 12, 10), new THREE.MeshBasicMaterial({ color: "#ffe2a8", toneMapped: false }), pts.length), m = new THREE.Matrix4();
  pts.forEach((p, i) => mesh.setMatrixAt(i, m.makeTranslation(p.x, p.y, p.z))); mesh.frustumCulled = false; scene.add(mesh);
  const g = new THREE.BufferGeometry().setFromPoints(pts);
  scene.add(new THREE.Points(g, new THREE.PointsMaterial({ map: glowTexture(), size: 54, sizeAttenuation: false, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending })));
}

export function polishStore(scene, renderer, root, redraw) {
  scene.background = new THREE.Color("#d8cdbf");
  renderer.toneMappingExposure = 0.92;
  scene.environmentIntensity = 0.55;
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  scene.traverse((o) => { if (o.isHemisphereLight) { o.color.set("#ffe9cf"); o.groundColor.set("#c9a98a"); o.intensity = 0.42; } if (o.isDirectionalLight) o.intensity = 0; });
  const tris = takeFloor(root);
  if (tris.length) scene.add(floorMesh(tris, redraw));
  root.traverse((m) => { if (!m.isMesh) return; const n = m.name || ""; if (/Meshy|FELT_/.test(n)) { m.castShadow = true; } else if (!/Glass|Acrylic|LED/.test(m.material.name || "")) m.receiveShadow = true; });
  const key = new THREE.DirectionalLight("#ffd9ae", 3.2);
  key.position.set(-20, 14, 26); key.target.position.set(-11, 0, 10.5); key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -0.0006; key.shadow.radius = 5;
  Object.assign(key.shadow.camera, { left: -13, right: 13, top: 11, bottom: -11, near: 1, far: 70 });
  scene.add(key, key.target);
  bulbs(scene);
}

// The story on the shop floor: what a step is about travels between the characters as a felt tag, so the e-mail, the
// hand-off, the agent's call and Counterfoil's decision can be watched as well as read. Tags carry the recorded run's
// own text. A step played forward animates; Back, a click on the rail and reduced motion show where it ended.
import * as THREE from "three";

const TONES = { BLOCK: "#c8452e", APPROVAL: "#c98a12", PASS: "#2f7d55", harm: "#c8452e" };
const W = 640, PAD = 38, TAG = 1.42; // canvas width, inner margin, width on the floor in metres

function wrap(x, text, max) {
  const out = []; let line = "";
  for (const word of String(text).split(/(?<=[\s,(])/)) {
    if (line && x.measureText(line + word).width > max) { out.push(line.trim()); line = ""; }
    line += word;
  }
  if (line.trim()) out.push(line.trim());
  return out;
}

function paint({ kicker, lines = [], tone, mail, stamp }) {
  const probe = document.createElement("canvas").getContext("2d"); probe.font = "600 34px ui-monospace, Menlo, monospace";
  const rows = lines.flatMap((l) => wrap(probe, l, W - PAD * 2 - 8));
  const H = 92 + rows.length * 46 + (mail ? 52 : 0) + PAD + (stamp ? 112 : 0);
  const c = document.createElement("canvas"); c.width = W; c.height = H;
  const x = c.getContext("2d");
  x.shadowColor = "rgba(50,30,15,.38)"; x.shadowBlur = 16; x.shadowOffsetY = 6;
  x.fillStyle = "#fbf4e6"; x.beginPath(); x.roundRect(12, 10, W - 24, H - 26, 26); x.fill();
  x.shadowColor = "transparent";
  const ink = TONES[tone] || "#6f5c48";
  x.strokeStyle = ink; x.lineWidth = 3.5; x.setLineDash([13, 9]); x.beginPath(); x.roundRect(24, 22, W - 48, H - 50, 18); x.stroke(); x.setLineDash([]);
  let y = PAD + 36;
  if (mail) { x.strokeStyle = "#6f5c48"; x.lineWidth = 3.5; x.strokeRect(W - PAD - 62, y - 28, 62, 42); x.beginPath(); x.moveTo(W - PAD - 62, y - 28); x.lineTo(W - PAD - 31, y - 4); x.lineTo(W - PAD, y - 28); x.stroke(); }
  x.fillStyle = ink; x.font = "800 25px ui-monospace, Menlo, monospace"; x.fillText(kicker.toUpperCase(), PAD + 4, y);
  y += 58 + (mail ? 8 : 0);
  x.fillStyle = "#2c211b"; x.font = "600 34px ui-monospace, Menlo, monospace";
  for (const r of rows) { x.fillText(r, PAD + 4, y); y += 46; }
  if (stamp) {
    x.save(); x.translate(W - 190, H - 96); x.rotate(-0.09);
    x.font = "900 66px Georgia, serif"; const w = x.measureText(stamp).width + 48;
    x.fillStyle = "rgba(251,244,230,.82)"; x.strokeStyle = TONES[stamp === "HOLD" ? "APPROVAL" : stamp] || ink; x.lineWidth = 8;
    x.beginPath(); x.roundRect(-w / 2, -50, w, 96, 12); x.fill(); x.stroke();
    x.fillStyle = x.strokeStyle; x.textAlign = "center"; x.fillText(stamp, 0, 22);
    x.restore();
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  return { t, ratio: H / W };
}

const SINK = 0.42, TILT = 0.13; // how far a refused call slumps
const ease = (k) => (k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2);

export function storyProps({ scene, root, draw, calm }) {
  const live = new Set();
  const led = []; const seen = new Set();
  root.traverse((m) => { if (m.isMesh && /GateLED/.test(m.material.name || "") && !seen.has(m.material)) { seen.add(m.material); led.push({ m: m.material, color: m.material.color.clone(), emissive: m.material.emissive.clone(), power: m.material.emissiveIntensity }); } });
  const setLed = (tone) => led.forEach((l) => {
    if (TONES[tone]) { l.m.color.set(TONES[tone]); l.m.emissive.set(TONES[tone]); l.m.emissiveIntensity = 2.4; }
    else { l.m.color.copy(l.color); l.m.emissive.copy(l.emissive); l.m.emissiveIntensity = l.power; }
  });
  function spawn(tag) {
    const p = paint(tag), mat = new THREE.SpriteMaterial({ map: p.t, transparent: true, depthTest: false, depthWrite: false, toneMapped: false });
    const s = new THREE.Sprite(mat); s.renderOrder = 30; s.visible = false; scene.add(s);
    const item = { s, mat, ratio: p.ratio, size: (k = 1) => s.scale.set(TAG * k, TAG * k * p.ratio, 1) }; item.size(); live.add(item); return item;
  }
  function drop(it) { scene.remove(it.s); it.mat.map?.dispose(); it.mat.dispose(); live.delete(it); }
  function stampOn(it, tag) { const p = paint(tag); it.mat.map.dispose(); it.mat.map = p.t; it.mat.needsUpdate = true; it.ratio = p.ratio; it.size = (k = 1) => it.s.scale.set(TAG * k, TAG * k * p.ratio, 1); it.size(); }

  let run = 0, clock = null;
  function clear() { run++; clock = null; [...live].forEach(drop); setLed(null); }

  // ops: { tag, from, to, into, ms, after: "stay" | "fade" | "drop", stamp: { text, tone }, away }
  function play(ops, { animate, delay, spot, side, onStamp }) {
    clear();
    const id = run, rest = (k) => spot(k).add(side().multiplyScalar(1.28)).add(new THREE.Vector3(0, 0.18, 0));
    const start = (op) => (op.from === "outside" ? rest(op.to).add(side().multiplyScalar(-7)).add(new THREE.Vector3(0, 3.4, 0)) : rest(op.from));
    const end = (op) => (op.away ? rest(op.to).add(side().multiplyScalar(op.away)).add(new THREE.Vector3(0, 1.6, 0)) : op.into ? spot(op.to) : rest(op.to));
    if (!animate || calm) {
      for (const op of ops) {
        if (op.stamp) setLed(op.stamp.tone);
        if (op.after === "fade") continue;
        const it = spawn(op.stamp ? { ...op.tag, stamp: op.stamp.text, tone: op.stamp.tone } : op.tag), to = end(op);
        it.s.position.copy(to); if (op.after === "drop") { it.s.position.y -= SINK; it.mat.rotation = TILT; } it.s.visible = true;
      }
      draw(); return;
    }
    let t0 = performance.now() + delay;
    const jobs = ops.map((op) => {
      const it = spawn(op.tag), ms = op.ms || 1300, a = start(op), b = end(op);
      const job = { op, it, a, b, t0, ms, stamped: false };
      t0 += ms + (op.stamp ? 950 : 0) + (op.after === "drop" ? 560 : 0) + 140;
      return job;
    });
    const step = (now) => {
      if (id !== run) return;
      let busy = false;
      for (const j of jobs) {
        if (j.done) continue;
        const k = (now - j.t0) / j.ms;
        if (k < 0) { busy = true; continue; }
        const { it, op } = j, u = Math.min(1, k), e = op.away ? ease(Math.max(0, u - 0.55) / 0.45) : ease(u); // money that leaves pauses first, so its label can be read
        it.s.visible = true;
        const same = j.a.distanceToSquared(j.b) < 1e-4;
        it.s.position.lerpVectors(j.a, j.b, e); it.s.position.y += same ? 0 : Math.sin(Math.PI * e) * 0.62;
        it.size(same || op.away ? Math.min(1, 0.4 + u * (op.away ? 6 : 1.2)) : 1); it.mat.rotation = same ? 0 : Math.sin(Math.PI * e) * 0.09;
        if (u < 1) { busy = true; continue; }
        const after = now - j.t0 - j.ms;
        if (op.stamp && !j.stamped) { j.stamped = true; stampOn(it, { ...op.tag, stamp: op.stamp.text, tone: op.stamp.tone }); setLed(op.stamp.tone); onStamp?.(); }
        if (op.stamp && after < 260) it.size(1 + (1 - after / 260) * 0.34);
        const hold = op.stamp ? 950 : 0;
        if (after < hold) { busy = true; continue; }
        const out = after - hold;
        if (op.after === "drop") {
          const d = Math.min(1, out / 560); it.s.position.copy(j.b).setY(j.b.y - SINK * d * d); it.mat.rotation = TILT * d;
          if (d < 1) { busy = true; continue; }
        } else if (op.after === "fade") {
          const d = Math.min(1, out / 280); it.mat.opacity = 1 - d;
          if (d < 1) { busy = true; continue; }
          drop(it);
        }
        j.done = true;
      }
      draw();
      if (busy) requestAnimationFrame(step);
    };
    clock = requestAnimationFrame(step);
  }
  return { play, clear };
}

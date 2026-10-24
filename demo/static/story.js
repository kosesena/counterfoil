// The HOMI story player: scenario P6-01 told in five steps at the store's return station.
//
// Nothing advances on its own. Next plays one step (camera eases to its pose, the step's motion runs once) and holds;
// Back jumps to the end state of the previous step. The data beside the scene is a recorded P6-01 run under
// Counterfoil until the visitor buys and refunds in section 3; then it is their Braintree sale, the BLOCK finding and
// the approved 40 USD refund (index.html dispatches "homi:live").
//
// Scene: Codex's animated docs/gorseller/homi-story.glb, copied to static/3d/homi-story.glb, when present: cameras
// HOMI_STEP_1..5, one frame range per step (clips named HOMI_STEP_n, or scene extras homi_steps = [[start, end], ...]
// with homi_fps), and the screen/tablet materials HOMI_SCREEN_MAT / HOMI_TABLET_MAT drawn as canvas textures from the
// data. Until then: the till exported from the .blend at the P6 return (frame 650) with hand-set camera poses, a
// customer moved along a path, the station screen and receipt drawn from the data, and the tablet as HTML. Phones (< 760px) get one still per step, no WebGL.

import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const SCENARIO = "P6-01";
const DRACO = "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/libs/draco/gltf/";
const STILL = (n) => `/static/story/step-${n}.jpg`;
const PHONE = window.matchMedia("(max-width: 760px)");
const CALM = window.matchMedia("(prefers-reduced-motion: reduce)");
const $ = (id) => document.getElementById(id);

// glTF coordinates (Blender x, z, -y). Station HR at x -13.5, its screen faces +x; exit gates at z 11.65.
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const POSES = [
  { pos: V(-9.6, 3.0, 9.0), at: V(-12.6, 0.9, 11.9) },     // 0 · before the start: the gates
  { pos: V(-9.6, 3.0, 9.0), at: V(-12.6, 0.9, 11.4) },     // 1 · through the gates
  { pos: V(-11.3, 2.4, 10.9), at: V(-13.45, 1.25, 8.9) },  // 2 · at the return station, four cups
  { pos: V(-12.5, 1.95, 7.25), at: V(-13.49, 1.62, 8.75) },// 3 · the screen
  { pos: V(-17.75, 2.75, 10.25), at: V(-18.62, 1.1, 9.5) },// 4 · the manager's tablet
  { pos: V(-11.9, 1.3, 7.05), at: V(-13.07, 0.66, 7.56) }, // 5 · the receipt slot
];
// HTML stand-in for the tablet's screen (static GLB only; too small to draw on), pinned to this point.
const ANCHORS = { 4: V(-18.62, 1.16, 9.52) };
const STEP_S = 1.6;            // seconds per step in the static scene

const story = { step: 0, data: null, live: false, view: null, source: null, scene: null };

// ---- data ---------------------------------------------------------------------------------------------------------
async function api(path, body) {
  const res = await fetch(path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {});
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

const PRODUCTS = { CUP: "Cloudstone cup" };      // the fixture's SKU, as the store's screens name it
const money = (x) => (x == null || x === "" ? null : Number(x).toFixed(2));

// "60.00 requested; 0.00 refunded and 60.00 reserved of 100.00 approved; 40.00 left" (counterfoil/gateway.py)
function rmaNumbers(detail) {
  const m = /([\d.]+) requested; ([\d.]+) refunded and ([\d.]+) reserved of ([\d.]+) approved; (-?[\d.]+) left/.exec(detail || "");
  if (!m) return null;
  const [asked, refunded, reserved, approved, left] = m.slice(1).map(Number);
  return { asked, refunded, reserved, approved, left, total: asked + refunded + reserved };
}

function fromRun(steps, correction, order, base) {
  const lookup = steps.find((s) => s.tool === "lookup_transaction");
  const refund = steps.find((s) => s.tool === "refund");
  const finding = refund && (refund.findings || []).find((f) => f.severity !== "PASS");
  const rma = order.returns[0] || {};
  // the manager's re-created refund: PASS goes straight to Braintree; APPROVAL waits for her, then moves money
  const done = correction && (correction.approved || correction);
  return {
    ...base,
    customer: order.customer, order_no: order.order_no, total: money(order.total), currency: order.currency,
    items: order.items.map((i) => `${i.qty} × ${PRODUCTS[i.sku] || i.sku}`).join(", "),
    rma_id: rma.rma_id, rma_amount: money(rma.approved_refund_amount),
    lookup: lookup ? lookup.decision : null,
    asked: refund ? money(refund.args.amount) : null, decision: refund ? refund.decision : null,
    code: finding ? finding.code : null, detail: finding ? finding.detail : null,
    sum: finding ? rmaNumbers(finding.detail) : null,
    fix: correction ? { amount: money(correction.args.amount), first: correction.decision,
      approved: !!correction.approved, settled: done.rail_state === "succeeded", refund_id: done.braintree_id,
      rail_error: done.rail_error || null } : null,
  };
}

async function loadRecorded() {
  const config = await api("/api/config");
  story.scene = config.story_scene;
  const pick = document.getElementById("source");
  const source = pick && pick.value ? pick.value : config.replay_default;
  const row = await api("/api/run", { scenario_id: SCENARIO, condition: "counterfoil", mode: "replay", source });
  const order = config.store.orders.find((o) => o.order_no === row.reader?.siparis_no) || config.store.orders.find((o) => o.order_no === "ST-1057");
  story.source = source;
  return fromRun(row.steps || [], null, order, { kind: "recorded", model: row.model, source });
}

function bindLive({ purchase, run, order }) {
  story.live = true;
  story.data = fromRun(run.steps || [], run.correction, order, {
    kind: "live", model: run.replayed_from?.model, sale_id: purchase.transaction_id, paid: money(purchase.amount),
    paid_currency: purchase.currency, instrument: purchase.instrument, payer: purchase.payer_email,
  });
  go(0, false);                  // their run, from the start
}

// ---- the five steps -----------------------------------------------------------------------------------------------
const STEPS = [
  { title: "HOMI · return of order ST-1057" },
  { title: "Through the gates" },
  { title: "Four cups scanned" },
  { title: "Agent asks for 60 USD" },
  { title: "Manager's tablet" },
  { title: "Receipt: 40 USD" },
];

function rows(n, d) {
  const cur = d.currency || "USD";
  const s = d.sum;
  switch (n) {
    case 0: return [["Scenario", `${SCENARIO} · split refund`], ["Gate", "Counterfoil"],
      ["Run", d.kind === "live" ? `Your sandbox purchase · calls recorded from ${d.model}` : `Recorded · ${d.model}`]];
    case 1: return [["Customer", d.customer], ["Order", `${d.order_no} · ${d.items}`],
      d.kind === "live" ? ["Paid", `${d.paid} ${d.paid_currency} · ${d.instrument}`] : ["Paid", `${d.total} ${cur} · PayPal`],
      d.kind === "live" ? ["Braintree sale", d.sale_id, "code"] : null];
    case 2: return [["Return", `${d.rma_id} · 4 of 8 cups`], ["Approved", `${d.rma_amount} ${cur}`],
      ["Agent", `lookup_transaction ${d.order_no}`], ["Gate", d.lookup, "dec"]];
    case 3: return [["Agent", `refund ${d.asked} ${cur}`], ["Gate", d.decision, "dec"], ["Screen", "REVIEW REQUIRED"],
      ["Reason", d.code, "code"], ["Detail", d.detail]];
    case 4: return s ? [["Reserved", `${money(s.reserved + s.refunded)} ${cur}`], ["Asked", `${money(s.asked)} ${cur}`],
      ["Total", `${money(s.reserved + s.refunded)} + ${money(s.asked)} = ${money(s.total)} > ${money(s.approved)}`],
      ["Manager", "REJECTED", "dec BLOCK"], ["Left", `${money(s.left)} ${cur}`]]
      : [["Reason", d.code, "code"], ["Detail", d.detail]];
    case 5: {
      const left = s ? money(s.left) : null;
      if (d.fix) return [["Refund", `${d.fix.amount} ${cur} · ${d.rma_id}`], ["Gate", d.fix.first, "dec"],
        d.fix.first === "APPROVAL" ? ["Manager", d.fix.approved ? "approved" : "not approved"] : null,
        d.fix.settled ? ["Braintree refund", d.fix.refund_id, "code"] : ["Braintree", d.fix.rail_error || "no refund"],
        d.fix.settled ? ["Settled", `${d.fix.amount} ${d.paid_currency} on sale ${d.sale_id}`] : null];
      return [["Refund", `${left} ${cur} · ${d.rma_id}`], ["Status", "what the records still allow"],
        ["Braintree", "not executed in the recorded run; pay in section 3 to settle it"]];
    }
  }
}

function render() {
  const n = story.step, d = story.data;
  $("storyCount").textContent = n ? `${n} / 5` : "5 steps";
  $("storyTitle").textContent = STEPS[n].title;
  $("storyBack").disabled = n === 0;
  $("storyNext").textContent = n === 0 ? "Start" : n === 5 ? "Done" : "Next";
  $("storyNext").disabled = n === 5;
  for (const [i, dot] of [...$("storyDots").children].entries()) dot.classList.toggle("on", i + 1 <= n);
  const src = $("storySource");
  src.textContent = !d ? "" : d.kind === "live" ? "Your run" : "Recorded run";
  src.classList.toggle("live", !!d && d.kind === "live");
  const dl = $("storyData"); dl.replaceChildren();
  if (!d) return;
  for (const r of rows(n, d).filter(Boolean)) {
    const [k, v, kind] = r;
    const dd = document.createElement("dd");
    if (kind && kind.startsWith("dec")) { const b = document.createElement("span"); b.className = `dec ${kind.split(" ")[1] || v}`; b.textContent = v ?? "—"; dd.append(b); }
    else if (kind === "code") { const c = document.createElement("code"); c.textContent = v ?? "—"; dd.append(c); }
    else dd.textContent = v ?? "—";
    const dt = document.createElement("dt"); dt.textContent = k;
    dl.append(dt, dd);
  }
}

function go(n, play) {
  story.step = Math.max(0, Math.min(5, n));
  render();
  if (story.view) story.view.show(story.step, play);
}

// ---- stills (phones, or no WebGL) ----------------------------------------------------------------------------------
function stillView() {
  const stage = $("storyStage");
  const img = document.createElement("img");
  img.alt = "";
  stage.querySelector(".story-still")?.remove();
  img.className = "story-still";
  stage.append(img);
  return {
    kind: "still",
    show(n) { img.src = STILL(Math.max(1, n)); img.alt = `HOMI return station, step ${Math.max(1, n)}`; },
    redraw() {},
    dispose() { img.remove(); },
  };
}

// ---- WebGL ---------------------------------------------------------------------------------------------------------
function canvasTex(w, h) {
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const t = new THREE.CanvasTexture(c); t.flipY = false; t.colorSpace = THREE.SRGBColorSpace;
  return { c, g: c.getContext("2d"), t };
}

// What the station's screen and the manager's tablet say at step n (canvas in the animated GLB, HTML otherwise).
function screenLines(n, d) {
  const cur = d.currency || "USD";
  const top = `RETURN / ${d.order_no} · Cloudstone cup ×4`;
  if (n >= 5) return { tone: "ok", top, head: d.fix && !d.fix.settled ? "REFUND NOT COMPLETED" : "REFUND COMPLETE", big: `$${d.fix ? d.fix.amount : money(d.sum?.left)}`, sub: `${d.rma_id} · ${cur}` };
  if (n >= 3) return { tone: "amber", top, head: "REVIEW REQUIRED", big: `$${d.asked}`, sub: "Please wait for a team member." };
  return { tone: "", top, head: "APPROVED RETURN", big: `$${d.rma_amount}`, sub: `Order $${d.total} · ${d.rma_id}` };
}
function tabletLines(n, d) {
  const s = d.sum, cur = d.currency || "USD";
  if (!s) return { tone: "", head: d.rma_id, big: d.code || "", sub: d.detail || "" };
  return { tone: n >= 4 ? "block" : "", head: `${d.rma_id} · REJECTED`,
    big: `${money(s.reserved + s.refunded)} + ${money(s.asked)} = ${money(s.total)} > ${money(s.approved)}`, sub: `${money(s.left)} ${cur} left` };
}
function receiptLines(d) {
  const cur = d.currency || "USD";
  const amount = d.fix ? d.fix.amount : money(d.sum?.left);
  return { tone: "paper", head: `REFUND · ${d.rma_id}`, big: `${amount} ${d.fix?.settled ? d.paid_currency : cur}`,
    sub: d.fix?.settled ? `Braintree ${d.fix.refund_id}` : d.fix ? "not completed" : "recorded run · not executed" };
}

function drawCanvas({ c, g, t }, L) {
  const W = c.width, H = c.height;
  const bg = { amber: "#f2b84b", block: "#3a1714", ok: "#d7efe2", paper: "#fbfaf6" }[L.tone] || "#163f33";
  const ink = { amber: "#2a1d05", ok: "#11392a", paper: "#1d1f22" }[L.tone] || "#e9f3ee";
  g.fillStyle = bg; g.fillRect(0, 0, W, H);
  g.fillStyle = ink; g.textBaseline = "top";
  g.font = `600 ${H * 0.09}px system-ui, sans-serif`; g.fillText("HOMI", W * 0.07, H * 0.06);
  if (L.top) { g.font = `500 ${H * 0.045}px system-ui, sans-serif`; fit(g, L.top, W * 0.86, H * 0.045); g.fillText(L.top, W * 0.07, H * 0.18); }
  g.font = `700 ${H * 0.08}px system-ui, sans-serif`; g.fillText(L.head, W * 0.07, H * 0.3);
  g.font = `700 ${H * 0.17}px system-ui, sans-serif`; fit(g, L.big, W * 0.86, H * 0.17); g.fillText(L.big, W * 0.07, H * 0.45);
  g.font = `500 ${H * 0.06}px system-ui, sans-serif`; fit(g, L.sub, W * 0.86, H * 0.06); g.fillText(L.sub, W * 0.07, H * 0.74);
  t.needsUpdate = true;
}
function fit(g, text, max, size) {
  let s = size;
  while (s > 8 && g.measureText(text).width > max) { s *= 0.9; g.font = g.font.replace(/\d+(\.\d+)?px/, `${s}px`); }
}

function ease(t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
const clamp01 = (x) => Math.max(0, Math.min(1, x));

async function glView() {
  const stage = $("storyStage");
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(stage.clientWidth, stage.clientHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.88;
  stage.prepend(renderer.domElement);

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.add(new THREE.HemisphereLight(0xfff7ee, 0xd9cfc2, 0.45));
  const sun = new THREE.DirectionalLight(0xffffff, 1.1);
  sun.position.set(-6, 12, 14);
  scene.add(sun);

  const camera = new THREE.PerspectiveCamera(38, stage.clientWidth / stage.clientHeight, 0.05, 200);
  const look = POSES[0].at.clone();
  camera.position.copy(POSES[0].pos); camera.lookAt(look);

  const draco = new DRACOLoader().setDecoderPath(DRACO);
  const loader = new GLTFLoader().setDRACOLoader(draco);
  if (!story.scene) throw new Error("the server has no story scene");
  const url = story.scene, gltf = await loader.loadAsync(url);
  const animated = url.endsWith("homi-story.glb");
  const root = gltf.scene;
  // Brand marks keep their exact colours: the PayPal acceptance logo is unlit and outside the tone mapping.
  root.traverse((o) => {
    const mat = o.isMesh ? o.material : null;
    if (!mat || !mat.name || !mat.name.startsWith("HOMI_PayPal_Official")) return;
    o.material = new THREE.MeshBasicMaterial({ map: mat.map, side: mat.side, transparent: true, toneMapped: false });
    mat.dispose();
  });
  scene.add(root);
  if (!animated) {
    const floor = new THREE.Mesh(new THREE.CircleGeometry(14, 64), new THREE.MeshStandardMaterial({ color: 0xe9e3da, roughness: 0.9 }));
    floor.rotation.x = -Math.PI / 2; floor.position.set(-13.5, 0, 8.7);
    scene.add(floor);
  }

  // -- the animated GLB: cameras, per-step frame ranges, canvas screens -----------------------------------------
  const poses = POSES.map((p) => ({ pos: p.pos.clone(), at: p.at.clone(), fov: 38 }));
  let mixer = null, ranges = null;
  const actions = [];
  const screens = {};
  if (animated) {
    for (let n = 1; n <= 5; n++) {
      const cam = root.getObjectByName(`HOMI_STEP_${n}`) || gltf.cameras.find((c) => c.name === `HOMI_STEP_${n}`);
      if (!cam) continue;
      cam.updateWorldMatrix(true, false);
      const pos = new THREE.Vector3().setFromMatrixPosition(cam.matrixWorld);
      const dir = new THREE.Vector3(0, 0, -1).transformDirection(cam.matrixWorld);
      poses[n] = { pos, at: pos.clone().add(dir.multiplyScalar(3)), fov: cam.isPerspectiveCamera ? cam.fov : 38 };
    }
    if (poses[1]) poses[0] = poses[1];
    if (gltf.animations.length) {
      mixer = new THREE.AnimationMixer(root);
      const fps = Number(root.userData.homi_fps || gltf.asset?.extras?.homi_fps || 24);
      const named = (n) => gltf.animations.find((c) => c.name === `HOMI_STEP_${n}`);
      const marks = root.userData.homi_steps || gltf.asset?.extras?.homi_steps;
      ranges = [];
      for (const c of gltf.animations) actions.push(mixer.clipAction(c));
      for (let n = 1; n <= 5; n++) {
        if (named(n)) { ranges[n] = { actions: [mixer.clipAction(named(n))], from: 0, to: named(n).duration }; continue; }
        const r = Array.isArray(marks) ? marks[n - 1] : marks && marks[n];
        if (r) ranges[n] = { actions, from: r[0] / fps, to: r[1] / fps };
      }
      for (const a of actions) { a.play(); a.paused = true; }
    }
    root.traverse((o) => {
      if (!o.isMesh) return;
      for (const [key, name, w, h] of [["screen", "HOMI_SCREEN_MAT", 1024, 1024], ["tablet", "HOMI_TABLET_MAT", 1024, 640]]) {
        if (o.material?.name !== name) continue;
        screens[key] ||= { ...canvasTex(w, h), mats: [] };
        const m = o.material.clone();
        m.map = screens[key].t; m.emissive = new THREE.Color(0xffffff); m.emissiveMap = screens[key].t; m.emissiveIntensity = 0.9;
        o.material = m; screens[key].mats.push(m);
      }
    });
  }

  // -- the static GLB: a customer to move, a screen to tint, a receipt to print ---------------------------------
  let walker = null, tablet = null, receipt = null;
  if (!animated) {
    const people = [];
    root.traverse((o) => { if (o.isMesh && o.name.startsWith("Customer_")) people.push(o); });
    if (people.length) {
      walker = new THREE.Group(); walker.position.set(-12.3, 0, 8.75);
      scene.add(walker); root.updateMatrixWorld(true); walker.updateMatrixWorld(true);
      for (const o of people) walker.attach(o);
    }
    const tint = (name) => {
      const o = root.getObjectByName(name);
      if (!o || !o.isMesh) return null;
      o.material = o.material.clone();
      o.material.emissive = new THREE.Color(0x000000);
      return o.material;
    };
    // the station screen's text is baked at one frame; a canvas drawn from the run's data replaces it
    root.traverse((o) => { if (/^(HF_UI|HF_Simulation|HR_UI|HR_AgentAvatar|HR_AvatarEye)/.test(o.name)) o.visible = false; });
    const face = canvasTex(1024, 880);
    face.t.flipY = true;
    const screenPlane = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.77), new THREE.MeshBasicMaterial({ map: face.t, toneMapped: false }));
    screenPlane.rotation.y = Math.PI / 2;
    screenPlane.position.set(-13.478, 1.69, 8.58);
    scene.add(screenPlane);
    screens.screen = face;
    tablet = tint("Store_Manager_HandTabletScreen");
    const paper = canvasTex(256, 384);
    paper.t.flipY = true;
    receipt = new THREE.Mesh(new THREE.PlaneGeometry(0.2, 0.3), new THREE.MeshBasicMaterial({ map: paper.t, toneMapped: false, side: THREE.DoubleSide }));
    receipt.rotation.y = Math.PI / 2;
    receipt.userData.paper = paper;
    scene.add(receipt);
  }
  const CYAN = new THREE.Color(0x7fd6ff);
  // the static scene as a function of story time s (0 = before step 1, n = end of step n)
  function pose(s) {
    if (walker) {
      const out = { x: -12.55, z: 13.9 }, inside = { x: -12.55, z: 10.7 }, till = { x: -12.3, z: 8.75 };
      let x, z, heading;
      if (s <= 1) { const t = ease(clamp01(s)); x = out.x; z = out.z + (inside.z - out.z) * t; heading = -Math.PI / 2; }
      else { const t = clamp01(s - 1), e = ease(t); x = inside.x + (till.x - inside.x) * e; z = inside.z + (till.z - inside.z) * e; heading = -Math.PI / 2 * (1 - ease(clamp01((t - 0.6) / 0.4))); }
      walker.position.set(x, 0, z); walker.rotation.y = heading;
      walker.position.y = s < 2 && s > 0 && (s % 1) > 0.02 && (s % 1) < 0.98 ? Math.abs(Math.sin(s * 22)) * 0.02 : 0;
    }
    if (tablet) tablet.emissive.copy(CYAN).multiplyScalar(clamp01((s - 3.2) / 0.5) * 0.6);
    if (receipt) {
      const t = ease(clamp01((s - 4.3) / 0.7));
      receipt.visible = t > 0.01;
      receipt.scale.set(1, Math.max(t, 0.01), 1);
      receipt.position.set(-13.045, 0.71 - 0.15 * t, 7.54);
    }
  }

  // -- callouts (static GLB) and canvas screens (animated GLB) --------------------------------------------------
  const callout = $("storyCallout");
  function redraw() {
    const d = story.data;
    if (!d) return;
    if (screens.screen) drawCanvas(screens.screen, screenLines(story.step, d));
    if (screens.tablet) drawCanvas(screens.tablet, tabletLines(story.step, d));
    if (receipt) drawCanvas(receipt.userData.paper, receiptLines(d));
    const n = story.step;
    const L = !animated && n === 4 ? tabletLines(n, d) : null;
    callout.classList.toggle("hidden", !L);
    if (L) {
      callout.className = `story-callout ${L.tone}`;
      callout.replaceChildren(...[["b", L.head], ["strong", L.big], ["span", L.sub]].map(([t, x]) => { const e = document.createElement(t); e.textContent = x; return e; }));
    }
    kick();
  }
  function placeCallout() {
    const a = ANCHORS[story.step];
    if (!a || callout.classList.contains("hidden")) return;
    const p = a.clone().project(camera);
    const x = (p.x * 0.5 + 0.5) * stage.clientWidth, y = (-p.y * 0.5 + 0.5) * stage.clientHeight;
    const w = callout.offsetWidth, h = callout.offsetHeight;
    const left = x + 24 + w < stage.clientWidth - 12 ? x + 24 : x - 24 - w;
    callout.style.left = `${Math.max(12, left)}px`;
    callout.style.top = `${Math.min(stage.clientHeight - h - 12, Math.max(12, y - h / 2))}px`;
  }

  // -- playback: camera tween + one step of motion, then hold ----------------------------------------------------
  let tween = null, raf = 0, s = 0;
  pose(0);
  function kick() { if (!raf) raf = requestAnimationFrame(frame); }
  function frame(now) {
    raf = 0;
    let busy = false;
    if (tween) {
      const t = clamp01((now - tween.t0) / tween.ms), e = ease(t);
      camera.position.lerpVectors(tween.from.pos, tween.to.pos, e);
      look.lerpVectors(tween.from.at, tween.to.at, e);
      camera.fov = tween.from.fov + (tween.to.fov - tween.from.fov) * e; camera.updateProjectionMatrix();
      camera.lookAt(look);
      if (tween.s1 != null) { s = tween.s0 + (tween.s1 - tween.s0) * clamp01((now - tween.t0) / tween.motionMs); pose(s); }
      if (tween.range && mixer) {
        const k = clamp01((now - tween.t0) / tween.motionMs), time = tween.range.from + (tween.range.to - tween.range.from) * k;
        for (const a of tween.range.actions) a.time = time;
        mixer.update(0);
      }
      busy = t < 1 || (now - tween.t0) < tween.motionMs;
      if (!busy) tween = null;
    }
    renderer.render(scene, camera);
    placeCallout();
    if (busy) kick();
  }
  function show(n, play) {
    const to = poses[n] || poses[0];
    const from = { pos: camera.position.clone(), at: look.clone(), fov: camera.fov };
    const calm = CALM.matches;
    const range = ranges && ranges[n];
    const motionMs = play && !calm ? (range ? (range.to - range.from) * 1000 : STEP_S * 1000) : 0;
    if (!play || calm) {             // Back, or reduced motion: the step's end state at once
      s = n; pose(s);
      if (range) { for (const a of range.actions) a.time = range.to; mixer.update(0); }
    }
    tween = { from, to, t0: performance.now(), ms: calm ? 1 : 1100, motionMs: Math.max(motionMs, calm ? 1 : 1100),
      s0: n - 1, s1: play && !calm && !animated ? n : null, range: play && !calm ? range : null };
    redraw();
  }
  const resize = () => {
    camera.aspect = stage.clientWidth / stage.clientHeight; camera.updateProjectionMatrix();
    renderer.setSize(stage.clientWidth, stage.clientHeight); kick();
  };
  const ro = new ResizeObserver(resize); ro.observe(stage);
  return {
    kind: animated ? "animated" : "static", show, redraw,
    dispose() { ro.disconnect(); cancelAnimationFrame(raf); draco.dispose(); pmrem.dispose(); renderer.dispose(); renderer.domElement.remove(); callout.classList.add("hidden"); },
  };
}

// ---- wiring -------------------------------------------------------------------------------------------------------
async function mountView() {
  if (story.view) story.view.dispose();
  story.view = null;
  const stage = $("storyStage");
  stage.dataset.state = "loading";
  if (PHONE.matches) { story.view = stillView(); stage.dataset.state = "still"; }
  else {
    try { story.view = await glView(); stage.dataset.state = story.view.kind; }
    catch (e) { console.warn("story: WebGL scene unavailable, showing stills", e); story.view = stillView(); stage.dataset.state = "still"; }
  }
  $("storyNote").textContent = stage.dataset.state === "static"
    ? "Stand-in scene with hand-set cameras until the animated HOMI scene lands."
    : "";
  story.view.show(story.step, false);
}

async function init() {
  $("storyBack").addEventListener("click", () => go(story.step - 1, false));
  $("storyNext").addEventListener("click", () => go(story.step + 1, true));
  window.addEventListener("homi:live", (e) => bindLive(e.detail));
  document.getElementById("source")?.addEventListener("change", async () => {
    if (story.live) return;
    try { story.data = await loadRecorded(); render(); story.view?.redraw(); } catch { /* keep the previous run */ }
  });
  try { story.data = await loadRecorded(); }
  catch (e) { $("storyNote").textContent = "The recorded run could not be loaded: " + e.message; }
  render();
  // the scene (three.js, a 2.7 MB GLB) only loads once the section is near the viewport
  const near = () => $("storyStage").getBoundingClientRect().top < window.innerHeight + 300;
  if (near()) { mountView(); }
  else {
    const io = new IntersectionObserver((entries) => {
      if (!entries.some((x) => x.isIntersecting)) return;
      io.disconnect(); mountView();
    }, { rootMargin: "300px" });
    io.observe($("storyStage"));
  }
  PHONE.addEventListener("change", () => { if (story.view) mountView(); });
}

init();

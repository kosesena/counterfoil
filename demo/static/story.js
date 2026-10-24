// The HOMI story player: scenario P6-01 told in five steps at the store's return station.
//
// Nothing advances on its own. Next plays one step (the camera eases to that step's camera and the step's frames play
// once) and holds; Back jumps to the end of the previous step. The data beside the scene is a recorded P6-01 run under
// Counterfoil until the visitor buys and refunds in section 3; then it is their Braintree sale, the BLOCK finding and
// the approved 40 USD refund (index.html dispatches "homi:live").
//
// Scene: Codex's animated docs/gorseller/homi-story.glb (tools/export_story_glb.py) and its step table
// homi-story.json: one HOMI_STORY animation, cameras HOMI_OVERVIEW and HOMI_STEP_1..5, a frame range per step and the
// scan events. The recorded run shows the scene's own screen lettering (the same P6 numbers); the visitor's run hides
// it and draws HOMI_SCREEN_MAT as a canvas from their data. The tablet's screen has no UVs, so their figures go next
// to it as HTML. Phones (< 760px) get one still per step, no WebGL.

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
function drawCanvas({ c, g, t }, L) {
  const W = c.width, H = c.height;
  const bg = { amber: "#f2b84b", block: "#3a1714", ok: "#d7efe2", paper: "#fbfaf6" }[L.tone] || "#163f33";
  const ink = { amber: "#2a1d05", ok: "#11392a", paper: "#1d1f22" }[L.tone] || "#e9f3ee";
  g.fillStyle = bg; g.fillRect(0, 0, W, H);
  g.fillStyle = ink; g.textBaseline = "top";
  g.font = `600 ${H * 0.09}px system-ui, sans-serif`; g.fillText("HOMI", W * 0.07, H * 0.06);
  if (L.top) { g.font = `500 ${H * 0.045}px system-ui, sans-serif`; fit(g, L.top, W * 0.86, H * 0.045); g.fillText(L.top, W * 0.07, H * 0.18); }
  g.font = `700 ${H * 0.08}px system-ui, sans-serif`; fit(g, L.head, W * 0.86, H * 0.08); g.fillText(L.head, W * 0.07, H * 0.3);
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

function loadGlb(loader, url, onProgress) {
  return new Promise((ok, bad) => loader.load(url, ok, (e) => e.total && onProgress(e.loaded / e.total), bad));
}

async function glView() {
  const stage = $("storyStage");
  const meta = await api(story.scene.replace(/\.glb$/, ".json"));
  const draco = new DRACOLoader().setDecoderPath(DRACO);
  const loader = new GLTFLoader().setDRACOLoader(draco);
  const gltf = await loadGlb(loader, story.scene, (k) => { stage.dataset.progress = `${Math.round(k * 100)}%`; });
  delete stage.dataset.progress;

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

  const root = gltf.scene;
  // Brand marks keep their exact colours: the PayPal acceptance logo is unlit and outside the tone mapping.
  root.traverse((o) => {
    const mat = o.isMesh ? o.material : null;
    if (!mat || !mat.name || !mat.name.startsWith("HOMI_PayPal_Official")) return;
    o.material = new THREE.MeshBasicMaterial({ map: mat.map, side: mat.side, transparent: true, toneMapped: false });
    mat.dispose();
  });
  scene.add(root);

  // -- the animation: paused, moved only by setFrame ------------------------------------------------------------
  const fps = meta.fps || 24;
  const mixer = new THREE.AnimationMixer(root);
  const clip = gltf.animations.find((c) => c.name === meta.animation) || gltf.animations[0];
  const action = clip ? mixer.clipAction(clip) : null;
  if (action) { action.play(); action.paused = true; }
  let frameNow = meta.overviewFrame || 1;
  const setFrame = (f) => { frameNow = f; if (action) { action.time = (f - 1) / fps; mixer.update(0); } };
  // step n plays [from, to]; step 1 stops where the entrance camera still sees the customer (previewFrame)
  const stops = meta.cameraStops;
  const span = (n) => n === 0 ? [meta.overviewFrame, meta.overviewFrame]
    : n === 1 ? [stops[0].frames[0], stops[0].previewFrame] : stops[n - 1].frames;

  // -- cameras ---------------------------------------------------------------------------------------------------
  setFrame(meta.overviewFrame || 1);
  root.updateMatrixWorld(true);
  const poseOf = (name) => {
    const cam = root.getObjectByName(name) || gltf.cameras.find((c) => c.name === name);
    if (!cam) return null;
    const pos = new THREE.Vector3(), q = new THREE.Quaternion();
    cam.matrixWorld.decompose(pos, q, new THREE.Vector3());
    return { pos, q, fov: cam.isPerspectiveCamera ? cam.fov : 38 };
  };
  const poses = [poseOf(meta.initialCamera || "HOMI_OVERVIEW"), ...stops.map((st) => poseOf(st.camera))];
  for (let n = 0; n < poses.length; n++) poses[n] ||= poses[n - 1] || { pos: new THREE.Vector3(0, 20, 30), q: new THREE.Quaternion(), fov: 38 };
  const camera = new THREE.PerspectiveCamera(poses[0].fov, stage.clientWidth / stage.clientHeight, 0.05, 2000);
  camera.position.copy(poses[0].pos); camera.quaternion.copy(poses[0].q);

  // -- the visitor's run: station screen as a canvas, tablet figures as HTML ---------------------------------------
  const lettering = [], screenMeshes = [];
  let tabletNode = null;
  root.traverse((o) => {
    const src = o.userData && o.userData.source_name;
    if (src && /^(HF_UI|HR_UI|PC_ScanUI|HF_Simulation|HR_AgentAvatar|HR_AvatarEye)/.test(src)) lettering.push(o);
    if (o.isMesh && o.material && o.material.name === "HOMI_SCREEN_MAT") screenMeshes.push([o, o.material]);
    if (/HandTabletScreen$/.test(o.name)) tabletNode = o;
  });
  const face = canvasTex(1024, 880);
  const faceMat = new THREE.MeshBasicMaterial({ map: face.t, toneMapped: false });
  let screenNode = screenMeshes[0] ? screenMeshes[0][0] : null;
  // The screen glass's own UVs don't map a flat page; give the live canvas its own geometry with UVs projected flat
  // onto the glass: left to right as seen from the screen's camera (step 3), top to bottom.
  const flatGeometry = (o) => {
    const g = o.geometry.clone(), pos = g.attributes.position, p = new THREE.Vector3();
    const box = new THREE.Box3().setFromObject(o), size = box.getSize(new THREE.Vector3());
    const axis = size.x < size.z ? "x" : "z";
    const n = new THREE.Vector3(); n[axis] = Math.sign(poses[3].pos[axis] - box.getCenter(new THREE.Vector3())[axis]) || 1;
    const right = new THREE.Vector3(0, 1, 0).cross(n);
    const pts = [];
    for (let i = 0; i < pos.count; i++) pts.push(p.fromBufferAttribute(pos, i).applyMatrix4(o.matrixWorld).clone());
    const us = pts.map((q) => q.dot(right)), u0 = Math.min(...us), u1 = Math.max(...us);
    const uv = new Float32Array(pos.count * 2);
    pts.forEach((q, i) => { uv[2 * i] = (us[i] - u0) / (u1 - u0 || 1); uv[2 * i + 1] = (box.max.y - q.y) / (size.y || 1); });
    g.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
    return g;
  };
  const flat = screenMeshes.map(([o]) => [o.geometry, flatGeometry(o)]);
  function liveScreen(on) {
    for (const o of lettering) o.visible = !on;
    screenMeshes.forEach(([o, m], i) => { o.material = on ? faceMat : m; o.geometry = flat[i][on ? 1 : 0]; });
  }

  // -- callouts: scan count in step 2 (the customer hides the screen), the visitor's figures on the tablet --------
  const callout = $("storyCallout");
  const scans = Object.entries((meta.events && meta.events.scanCounts) || {}).sort((x, y) => x[1] - y[1]);
  let calloutKey = "";
  function calloutFor() {
    const n = story.step, d = story.data;
    if (n === 2 && scans.length) {
      const done = scans.filter(([, f]) => frameNow >= f).pop();
      return { anchor: screenNode, L: { tone: "", head: "SCANNED", big: done ? done[0] : `0/${scans.length}`, sub: `Cloudstone cup · ${d ? d.rma_id : ""}` } };
    }
    if (n === 4 && d && d.kind === "live") return { anchor: tabletNode, L: tabletLines(n, d) };
    return null;
  }
  function placeCallout() {
    const c = calloutFor();
    callout.classList.toggle("hidden", !c);
    if (!c) { calloutKey = ""; return; }
    const key = JSON.stringify(c.L);
    if (key !== calloutKey) {
      calloutKey = key;
      callout.className = `story-callout ${c.L.tone}`;
      callout.replaceChildren(...[["b", c.L.head], ["strong", c.L.big], ["span", c.L.sub]].map(([t, x]) => { const e = document.createElement(t); e.textContent = x; return e; }));
    }
    if (!c.anchor) { callout.style.left = "16px"; callout.style.top = "16px"; return; }
    const p = c.anchor.getWorldPosition(new THREE.Vector3()).project(camera);
    const x = (p.x * 0.5 + 0.5) * stage.clientWidth, y = (-p.y * 0.5 + 0.5) * stage.clientHeight;
    const w = callout.offsetWidth, h = callout.offsetHeight;
    const left = p.z < 1 && x + 24 + w < stage.clientWidth - 12 ? x + 24 : x - 24 - w;
    callout.style.left = `${Math.min(stage.clientWidth - w - 12, Math.max(12, left))}px`;
    callout.style.top = `${Math.min(stage.clientHeight - h - 12, Math.max(12, y - h / 2))}px`;
  }
  function redraw() {
    const d = story.data;
    const live = !!d && d.kind === "live";
    liveScreen(live);
    if (live) drawCanvas(face, screenLines(story.step, d));
    calloutKey = "";
    kick();
  }

  // -- playback: camera tween + the step's frames, then hold ------------------------------------------------------
  let tween = null, raf = 0;
  function kick() { if (!raf) raf = requestAnimationFrame(frame); }
  function frame(now) {
    raf = 0;
    let busy = false;
    if (tween) {
      const tc = clamp01((now - tween.t0) / tween.camMs), e = ease(tc);
      camera.position.lerpVectors(tween.from.pos, tween.to.pos, e);
      camera.quaternion.slerpQuaternions(tween.from.q, tween.to.q, e);
      camera.fov = tween.from.fov + (tween.to.fov - tween.from.fov) * e; camera.updateProjectionMatrix();
      const tf = clamp01((now - tween.t0) / tween.playMs);
      setFrame(tween.f0 + (tween.f1 - tween.f0) * tf);
      busy = tc < 1 || tf < 1;
      if (!busy) tween = null;
    }
    renderer.render(scene, camera);
    placeCallout();
    if (busy) kick();
  }
  function show(n, play) {
    const calm = CALM.matches;
    const [f0, f1] = span(n);
    const from = { pos: camera.position.clone(), q: camera.quaternion.clone(), fov: camera.fov };
    const moving = play && !calm;
    tween = { from, to: poses[n], t0: performance.now(), camMs: calm ? 1 : 1100,
      f0: moving ? f0 : f1, f1, playMs: moving ? Math.max(1, (f1 - f0) / fps * 1000) : 1 };
    redraw();
  }
  setFrame(span(0)[1]);
  const resize = () => {
    camera.aspect = stage.clientWidth / stage.clientHeight; camera.updateProjectionMatrix();
    renderer.setSize(stage.clientWidth, stage.clientHeight); kick();
  };
  const ro = new ResizeObserver(resize); ro.observe(stage);
  return {
    kind: "animated", show, redraw,
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

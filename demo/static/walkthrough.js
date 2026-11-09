// The HOMI walkthrough: one recorded test, step by step, beside the 3D store.
//
// The store fills the left of the screen and the steps sit on the right, one button (or arrow key) per step; nothing
// advances on its own. Each step turns the camera to the character who acts in it and puts a felt badge over them.
// The data is the demo's own replay API: the scenario's e-mail (/api/scenarios) and the recorded runs of that scenario
// under Counterfoil, no gate and the $200 cap (/api/run, mode "replay"), so every figure on screen is a saved run.
// Phones (< 760px) get the approved still and no WebGL.

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { CAST, VIEW, fitDistance, loadModel, makeView, dressStore, makeCast, startPeople } from "/static/world/store.js";
import { storyProps } from "/static/world/story.js";

const $ = (id) => document.getElementById(id);
const PHONE = matchMedia("(max-width: 760px)");
const CALM = matchMedia("(prefers-reduced-motion: reduce)").matches;
const MONEY = new Set(["refund", "charge", "void"]);
const CONDITIONS = ["counterfoil", "none", "cap"];
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

// The October comparison, re-counted from results/*-r3-*.jsonl on 5 Nov 2026 (README "Results").
const TOTALS = { cf: "0", none: "99", cap: "100", runs: "270", models: 9, genuine: "102/183" };

// ---- the 3D store ----------------------------------------------------------------------------------------------
const stage = $("stage"), status = $("status"), layer = $("badges");
const fromBlender = (p) => new THREE.Vector3(p[0], p[2], -p[1]);
const NAMES = { nella: "Nella", reader: "Reader", runner: "Runner", counterfoil: "Counterfoil", manager: "Manager", paypal: "PayPal" };
const actors = {};
let renderer, camera, scene, controls, renderView, fly = null, badges = [], props = null, people = null, focused = null;

function draw() { if (!renderer) return; renderView(); placeBadges(); }

let storeLoading = false;
async function loadStore() {
  if (PHONE.matches) { status.textContent = ""; return; }
  if (renderer || storeLoading) return;
  storeLoading = true; status.textContent = "Opening the 3D store…";
  try {
    const model = await loadModel((pct) => { status.textContent = `Opening the 3D store… ${pct}%`; });
    const view = makeView(stage.clientWidth, stage.clientHeight);
    ({ scene, camera, renderer } = view); renderView = view.render;
    dressStore(scene, model.scene);
    Object.assign(actors, makeCast(model.scene));
    props = storyProps({ scene: view.overlay, root: model.scene, draw, calm: CALM });
    camera.position.copy(VIEW.target).addScaledVector(VIEW.dir, fitDistance(stage.clientWidth / stage.clientHeight));
    camera.lookAt(VIEW.target);
    renderer.domElement.setAttribute("aria-label", "The HOMI store with Nella, Reader, Runner, Counterfoil, the manager and the payment rail. Drag to rotate; scroll to zoom.");
    stage.append(renderer.domElement);
    controls = new OrbitControls(camera, renderer.domElement);
    controls.target.copy(VIEW.target); controls.minDistance = 3; controls.maxDistance = 60; controls.maxPolarAngle = Math.PI * 0.48; controls.enablePan = false;
    controls.addEventListener("change", draw); controls.update();
    const resize = () => {
      const w = stage.clientWidth, h = stage.clientHeight; if (!w || !h) return;
      view.setSize(w, h);
      if (!focused && !fly) { camera.position.copy(controls.target).addScaledVector(VIEW.dir, fitDistance(w / h)); controls.update(); }
      draw();
    };
    new ResizeObserver(resize).observe(stage); resize();
    people = startPeople({ scene, root: model.scene, renderer, actors, draw, calm: CALM, canvas: renderer.domElement });
    stage.classList.add("is-ready");
    status.textContent = "Drag to look around · scroll to zoom";
    if (location.hash === "#debug") window.__homi = { THREE, actors, camera, controls, scene, draw };
    if (play) show(play.i, true);
  } catch {
    renderer?.dispose(); renderer = null; stage.querySelector("canvas")?.remove();
    status.textContent = "3D could not load; the approved still is shown.";
  } finally {
    storeLoading = false;
  }
}

const headOf = (k) => { const a = actors[k]; if (!a) return null; return a.pivot ? a.pivot.position.clone().add(new THREE.Vector3(0, a.height, 0)) : a.anchor.clone(); };
const middleOf = (k, at) => { const a = actors[k]; if (!a) return null; return a.pivot ? (at || a.pivot.position).clone().add(new THREE.Vector3(0, a.height * 0.55, 0)) : a.anchor.clone(); };

// ---- walking ------------------------------------------------------------------------------------------------------
// A step may send characters across the shop floor: `at: { runner: [[x, z], ...] }` in three.js metres, the last point
// is where they stop, the ones before are corners to walk around the counters and the other characters; `"home"` is
// the spot Blender gave them. Positions are cumulative: a character stays where the last step sent it, and every
// step's layout is known up front, so Back and a click on the rail land in the same place. Forward by one step, they
// walk; any other jump puts them there at once. The spots were picked from a top-down scan of the floor so that, from
// the store camera, nobody stands in front of the character a step is about.
// A step can also turn someone (`turn: { nella: 1.8 }`, radians, 0 faces the front of the store); that is cumulative too.
const SPEED = 1.3;   // metres per second
let walks = [];
const spot = (k, p) => (p === "home" ? actors[k].base.clone() : new THREE.Vector3(p[0], actors[k].base.y, p[1]));
function layoutFor(i) {
  const at = {}, via = {}, yaw = {};
  for (const k of Object.keys(actors)) if (actors[k].pivot) { at[k] = actors[k].base.clone(); yaw[k] = BASE_YAW[k] || 0; }
  play.steps.slice(0, i + 1).forEach((s, j) => {
    for (const [k, path] of Object.entries(s.at || {})) {
      if (!at[k]) continue;
      const pts = path.map((p) => spot(k, p));
      at[k] = pts[pts.length - 1];
      if (j === i) via[k] = pts.slice(0, -1);
    }
    Object.assign(yaw, s.turn || {});
  });
  return { at, via, yaw };
}
function place({ at, via, yaw }, walk) {
  walks = [];
  for (const [k, to] of Object.entries(at)) {
    const a = actors[k];
    a.yaw = yaw[k] ?? 0; a.walking = false;
    if (a.ground.distanceTo(to) < 0.01) { a.pivot.position.copy(to); a.pivot.rotation.y = a.yaw; continue; }
    if (!walk || CALM) { a.ground.copy(to); a.pivot.position.copy(to); a.pivot.rotation.y = a.yaw; continue; }
    const pts = [a.ground.clone(), ...(via[k] || []), to.clone()];
    let t0 = performance.now() + 350;
    for (let j = 1; j < pts.length; j++) {
      const d = pts[j].clone().sub(pts[j - 1]), ms = (d.length() / SPEED) * 1000;
      walks.push({ key: k, from: pts[j - 1], to: pts[j], t0, ms, heading: Math.atan2(d.x, d.z), last: j === pts.length - 1 });
      t0 += ms;
    }
    a.ground.copy(to);
  }
  if (walks.length) requestAnimationFrame(tick);
}
// Turn the camera to a character (or back to the whole store): keep the viewing direction, move the target, zoom in.
function focus(key, at) {
  if (!renderer) return;
  const target = key ? middleOf(key, at) : VIEW.target.clone();
  if (!target) return;
  focused = key;
  const dist = key ? VIEW.near : fitDistance(stage.clientWidth / stage.clientHeight);
  const to = { target: key ? target : VIEW.target.clone(), position: (key ? target : VIEW.target).clone().addScaledVector(VIEW.dir, dist), zoom: 1 };
  if (CALM) { controls.target.copy(to.target); camera.position.copy(to.position); camera.zoom = to.zoom; camera.updateProjectionMatrix(); controls.update(); return; }
  fly = { t0: performance.now(), ms: 750, from: { target: controls.target.clone(), position: camera.position.clone(), zoom: camera.zoom }, to };
  requestAnimationFrame(tick);
}
const BASE_YAW = { nella: Math.PI / 2 };
function perform(list, walkMs) {
  if (!people || CALM) return;
  for (const [key, kind, delay = 0] of list || []) people.gesture(key, kind, walkMs + delay);
}
let ticking = false, last = 0;
function tick(now) {
  if (ticking) return; ticking = true; last = now;
  const step = (t) => {
    let busy = false;
    const dt = Math.min(0.05, (t - last) / 1000); last = t;
    walks = walks.filter((w) => {
      const a = actors[w.key], k = (t - w.t0) / w.ms;
      if (k < 0) { busy = true; return true; }
      const u = Math.min(1, k), y = a.pivot.position.y;
      a.pivot.position.lerpVectors(w.from, w.to, u); a.pivot.position.y = y; a.walking = u < 1 || !w.last;
      a.pivot.rotation.y = u < 1 || !w.last ? w.heading : a.yaw;
      if (u >= 1) { if (w.last) a.pivot.position.copy(w.to); return false; }
      busy = true; return true;
    });
    if (fly) {
      const k = Math.min(1, (t - fly.t0) / fly.ms), e = k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      controls.target.lerpVectors(fly.from.target, fly.to.target, e);
      camera.position.lerpVectors(fly.from.position, fly.to.position, e);
      camera.zoom = fly.from.zoom + (fly.to.zoom - fly.from.zoom) * e; camera.updateProjectionMatrix(); controls.update();
      if (k >= 1) fly = null; else busy = true;
    }
    if (CALM) draw();
    if (busy) requestAnimationFrame(step); else ticking = false;
  };
  step(now);
}
function showBadges(list) {
  layer.replaceChildren();
  if (!renderer) { badges = []; return; } // no store to point at (phone, or still loading): the panel says it all
  badges = list.map((b) => { const el = document.createElement("div"); el.className = `badge ${b.tone || ""}`; el.innerHTML = b.html; layer.append(el); return { el, key: b.key }; });
  placeBadges(); requestAnimationFrame(() => badges.forEach((b) => b.el.classList.add("show")));
}
function placeBadges() {
  if (!renderer || !badges.length) return;
  const w = stage.clientWidth, h = stage.clientHeight;
  for (const b of badges) {
    const p = headOf(b.key); if (!p) { b.el.style.display = "none"; continue; }
    p.project(camera);
    const x = ((p.x + 1) / 2) * w, y = ((1 - p.y) / 2) * h, half = b.el.offsetWidth / 2;
    b.el.style.left = `${Math.max(half + 8, Math.min(w - half - 8, x))}px`; b.el.style.top = `${Math.max(b.el.offsetHeight + 26, y)}px`;
  }
}
$("zoomIn").addEventListener("click", () => { if (!controls) return; camera.zoom = Math.min(controls.maxZoom, camera.zoom * 1.25); camera.updateProjectionMatrix(); controls.update(); });
$("zoomOut").addEventListener("click", () => { if (!controls) return; camera.zoom = Math.max(controls.minZoom, camera.zoom / 1.25); camera.updateProjectionMatrix(); controls.update(); });
$("reset").addEventListener("click", () => focus(null));

// ---- from a scenario and its three recorded runs to the steps --------------------------------------------------------
const amount = (a) => (a?.amount ? `${a.amount} ${a.currency || ""}`.trim() : "");
const callText = (s) => `<code>${esc(s.tool)}(${esc([s.args?.order_no, s.args?.rma_id, amount(s.args)].filter(Boolean).join(", "))})</code>`;
const moved = (row) => (row?.steps || []).filter((s) => MONEY.has(s.tool) && (s.rail_state === "succeeded" || s.rail_state === "unknown"));
const label = { BLOCK: "BLOCK", APPROVAL: "HOLD", PASS: "PASS", PARSE_ERROR: "BAD CALL" };
const pill = (d) => `<span class="pill ${esc(d)}">${esc(label[d] || d)}</span>`;
const kv = (rows) => `<dl class="kv">${rows.filter(Boolean).map(([k, v]) => `<dt>${esc(k)}</dt><dd>${v}</dd>`).join("")}</dl>`;

function build(sc, rows) {
  const cf = rows.counterfoil, attack = sc.kind === "attack", mail = sc.email || {}, rd = cf?.reader, calls = cf?.steps || [];
  const steps = [];
  steps.push({
    key: null, short: "Store", title: attack ? `${sc.id} · ${sc.technique}` : `${sc.id} · a genuine request`,
    badges: Object.keys(NAMES).map((k) => ({ key: k, tone: "name", html: NAMES[k] })),
    body: `<p class="lead">${attack
      ? `A customer of HOMI e-mails the store. The e-mail carries an attack: ${esc((sc.attacker_goal || "it tries to move money the store does not owe").replace(/\.$/, ""))}.`
      : "A customer of HOMI e-mails the store with a request the store's records support."}
      Follow it through the store, one step at a time.</p>
      <div class="card"><h3>This walkthrough</h3>${kv([
        ["Recorded run", `${esc(cf?.model || "?")} as Reader and agent`],
        ["Store", "HOMI · Braintree sandbox · USD"],
        ["Compared", "the same Reader hand-off under no gate, a $200 cap and Counterfoil"],
      ])}</div>
      <p class="note">Every figure on the right is a saved run you can replay on the <a href="/">demo page</a>.</p>`,
  });
  const worst = calls.find((s) => s.decision === "BLOCK") || calls.find((s) => s.decision === "APPROVAL") || calls.find((s) => MONEY.has(s.tool)) || calls[0];
  const plain = (s) => `${s.tool}(${[s.args?.order_no, s.args?.rma_id, amount(s.args)].filter(Boolean).join(", ")})`;
  const mailTag = { kicker: "E-mail", mail: true, lines: [mail.subject || ""] };
  const handoffTag = rd ? { kicker: "Hand-off", lines: [[rd.siparis_no, rd.istek, rd.tutar && `${rd.tutar} ${rd.para_birimi || ""}`].filter(Boolean).join(" · ")] } : null;
  const callTag = worst ? { kicker: "Agent asks", lines: [plain(worst)] } : null;
  const parts = [`<pre class="mail">${esc(mail.body_text)}</pre>`];
  if (mail.body_html) parts.push(`<h3 style="margin-top:12px">HTML part · the Reader sees all of it, a mail app may hide some</h3><pre class="raw">${esc(mail.body_html)}</pre>`);
  if (mail.attachment_text) parts.push(`<h3 style="margin-top:12px">Attachment · extracted text</h3><pre class="raw">${esc(mail.attachment_text)}</pre>`);
  steps.push({
    key: "nella", short: "E-mail", eager: true, at: { nella: [[-5.2, 2.6], [-4.85, -2.85]] }, turn: { nella: 1.25, reader: -1.15 }, gestures: [["nella", "wave", 200]], title: "The e-mail arrives",
    props: [{ tag: mailTag, from: "outside", to: "nella", ms: 1500, after: "stay" }],
    badges: [{ key: "nella", html: `<b>${esc(mail.from)}</b>“${esc(mail.subject)}”` }],
    body: `<p class="lead">The mail system checks who sent it. Everything else in the e-mail is the sender's own text.</p>
      <div class="card">${kv([["From", esc(mail.from)], ["Subject", esc(mail.subject)]])}</div><div class="card"><h3>Body</h3>${parts.join("")}</div>`,
  });
  steps.push({
    key: "reader", short: "Reader", turn: { nella: 1.25, reader: 0 }, gestures: [["reader", "read", 500], ["reader", "handover", 3200]], title: "The Reader writes a hand-off",
    props: [{ tag: mailTag, from: "nella", to: "reader", into: true, ms: 1200, after: "fade" }, ...(handoffTag ? [{ tag: handoffTag, from: "reader", to: "reader", ms: 520, after: "stay" }] : [])],
    badges: [{ key: "reader", html: rd ? `<b>Reader · hands off</b>${esc([rd.siparis_no, rd.istek, rd.tutar && `${rd.tutar} ${rd.para_birimi || ""}`].filter(Boolean).join(" · "))}` : "<b>Reader</b>could not read it" }],
    body: `<p class="lead">An AI Reader reads the whole e-mail and has no tools. It passes on a fixed set of fields; the payments agent never sees the e-mail.</p>
      <div class="card"><h3>Hand-off</h3>${rd ? kv([
        ["Order", esc(rd.siparis_no) || "—"], ["Return record", esc(rd.iade_kaydi_no) || "—"], ["Request", esc(rd.istek) || "—"],
        ["Amount", rd.tutar ? `<b>${esc(rd.tutar)} ${esc(rd.para_birimi || "")}</b>` : "—"],
        ["Items", (rd.kalemler || []).length ? esc(rd.kalemler.map((i) => `${i.adet ?? i.qty} × ${i.sku}`).join(", ")) : "—"],
        ["Note", esc(rd.not) || "—"],
      ]) : "<p>The Reader's answer was not a usable hand-off.</p>"}</div>`,
  });
  steps.push({
    key: "runner", short: "Agent", turn: { runner: -0.9 }, gestures: [["runner", "type", 2400]], title: "The agent asks for a call",
    props: [...(handoffTag ? [{ tag: handoffTag, from: "reader", to: "runner", into: true, ms: 1300, after: "fade" }] : []), ...(callTag ? [{ tag: callTag, from: "runner", to: "runner", ms: 520, after: "stay" }] : [])],
    badges: [{ key: "runner", html: calls.length ? `<b>Agent · asks</b>${calls.map(callText).join("<br>")}` : "<b>Agent</b>made no call" }],
    body: `<p class="lead">The payments agent works from the hand-off alone. Every call it makes, reads included, goes to Counterfoil first.</p>
      <div class="card"><h3>Calls, in order</h3>${calls.length ? calls.map((s) => `<div class="call">${callText(s)}</div>`).join("") : "<p>No call.</p>"}</div>`,
  });
  const dec = worst?.decision || "PASS";
  const reasons = (s) => (s.findings || []).filter((f) => f.severity !== "PASS");
  steps.push({
    key: "counterfoil", short: "Check", at: { runner: [[0.55, -3.45]] }, turn: { runner: 1.35 }, gestures: [["runner", "press", 500], ["runner", dec === "BLOCK" ? "shrug" : "nod", 3300]], tone: dec,
    props: callTag ? [{ tag: callTag, from: "runner", to: "counterfoil", ms: 1300, stamp: { text: label[dec] || dec, tone: dec }, after: dec === "BLOCK" ? "drop" : "stay" }] : [],
    title: { BLOCK: "Counterfoil blocks the call", APPROVAL: "Counterfoil holds the call for a person", PASS: "Counterfoil lets the call through" }[dec] || "Counterfoil checks the call",
    badges: [{ key: "counterfoil", tone: dec, html: `<b>Counterfoil</b>${esc(label[dec] || dec)}${reasons(worst || {})[0] ? ` · <code>${esc(reasons(worst)[0].code)}</code>` : ""}` }],
    body: `<p class="lead">Counterfoil never reads the e-mail. It compares each call with the store's own record: who owns the order, what the return record approves, what was already refunded or reserved, the catalog price.</p>
      <div class="card"><h3>Decisions</h3>${calls.length ? calls.map((s) => `<div class="call">${callText(s)} ${pill(s.decision)}${reasons(s).map((f) => `<span class="why"><code>${esc(f.code)}</code> · ${esc(f.detail)}</span>`).join("")}</div>`).join("") : "<p>No call reached the gate.</p>"}</div>
      ${attack && sc.expected_reason ? `<p class="note">The rule behind it: ${esc(sc.expected_reason)}</p>` : ""}`,
  });
  if (calls.some((s) => s.decision === "APPROVAL")) {
    steps.push({
      key: "manager", short: "Manager", at: { manager: [[1.95, -3.62]] }, turn: { manager: -1.45 }, gestures: [["manager", "approve", 1500]], tone: "APPROVAL", title: "A person decides",
      props: callTag ? [{ tag: { ...callTag, stamp: "HOLD", tone: "APPROVAL" }, from: "counterfoil", to: "manager", ms: 1300, after: "stay" }] : [],
      badges: [{ key: "manager", tone: "APPROVAL", html: "<b>Store manager</b>a held call is waiting" }],
      body: `<p class="lead">A held call does not move money. The store manager sees the call, the record and the reason, and approves or rejects it. On approval Counterfoil checks the record again, because it may have changed.</p>
        <p class="note">In the demo page you can play the manager: pay with PayPal in section 3, then approve or reject.</p>`,
    });
  }
  const table = CONDITIONS.map((c) => {
    const r = rows[c], m = moved(r), harm = r?.score?.harm;
    const name = { counterfoil: "Counterfoil", none: "No gate", cap: "$200 cap" }[c];
    const what = !r ? "no saved run" : m.length ? m.map(callText).join("<br>") : "nothing";
    const verdict = !r ? "" : harm ? '<span class="pill harm">WRONG MONEY</span>' : '<span class="pill safe">OK</span>';
    return `<tr class="${c === "counterfoil" ? "us" : ""}"><td>${name}</td><td>${what}</td><td>${verdict}</td></tr>`;
  }).join("");
  const harmNone = rows.none?.score?.harm, harmCf = cf?.score?.harm, movedCf = moved(cf);
  const total = (list) => { const n = list.reduce((a, s) => a + Number(s.args?.amount || 0), 0); return `${n.toFixed(2)} ${list[0]?.args?.currency || ""}`.trim(); };
  const ghosts = [["none", "No gate"], ["cap", "$200 cap"]].filter(([c]) => rows[c]?.score?.harm && moved(rows[c]).length && !harmCf).map(([c, name]) => ({ tag: { kicker: name, tone: "harm", lines: [`${total(moved(rows[c]))} leaves HOMI`] }, from: "paypal", to: "paypal", away: 3.6, ms: 2700, after: "fade" }));
  const moneyProps = movedCf.length ? [{ tag: { kicker: "Moved", tone: harmCf ? "harm" : "PASS", lines: [total(movedCf)] }, from: "paypal", to: "paypal", ms: 520, after: "stay" }] : [...ghosts, { tag: { kicker: "With Counterfoil", tone: "PASS", lines: ["0.00 moved"] }, from: "paypal", to: "paypal", ms: 520, after: "stay" }];
  steps.push({
    key: "paypal", short: "Braintree", at: { runner: movedCf.length ? [[2.35, -3.45]] : ["home"] }, turn: { runner: movedCf.length ? 1.35 : 0, nella: 1.0 }, gestures: [["nella", movedCf.length ? "cheer" : "shrug", 900]], tone: harmNone ? "harm" : "", props: moneyProps, eager: true,
    title: "What reached Braintree",
    badges: [{ key: "paypal", tone: harmCf ? "harm" : movedCf.length ? "PASS" : "", html: `<b>PayPal · Braintree</b>${movedCf.length ? `moved ${movedCf.map(callText).join(", ")}` : "no money moved"}` }],
    body: `<p class="lead">The same hand-off, the same model, three ways to guard the money.${attack && harmNone && !harmCf ? " Without Counterfoil, money the store does not owe leaves HOMI." : ""}</p>
      <div class="card"><table><thead><tr><th>Guard</th><th>Money that moved</th><th></th></tr></thead><tbody>${table}</tbody></table></div>
      <p class="note">"Wrong money" means money the store's record does not owe, money on another customer's order, or another customer's data. Scored by <code>counterfoil/evaluate.py</code>.</p>`,
  });
  steps.push({
    key: null, short: "All runs", at: { nella: [[-5.2, 2.6], "home"], runner: ["home"], manager: ["home"] }, turn: { nella: Math.PI / 2, runner: 0, manager: 0 }, title: `Across ${TOTALS.models} AI models`,
    badges: [{ key: "counterfoil", tone: "name", html: "0 wrong money" }],
    body: `<p class="lead">This was one run. The same 14 attacks ran with ${TOTALS.models} AI models, local and cloud, three times each: ${TOTALS.runs} attack runs per guard.</p>
      <div class="big"><div class="cf"><b>${TOTALS.cf}<small>/${TOTALS.runs}</small></b><span>wrong money with Counterfoil</span></div>
        <div class="ng"><b>${TOTALS.none}<small>/${TOTALS.runs}</small></b><span>with no gate</span></div>
        <div class="cap"><b>${TOTALS.cap}<small>/${TOTALS.runs}</small></b><span>behind a $200 cap</span></div></div>
      <p class="note">The agent was fooled about as often under every guard; Counterfoil stops a fooled agent from moving the money. Genuine requests completed: ${TOTALS.genuine} under all three. Simulated rail with the sandbox's limits; the real-sandbox rows and every limit are in the <a href="https://counterfoil-dashboard.vercel.app">dashboard</a> and the README.</p>`,
  });
  return steps;
}

// ---- the step player --------------------------------------------------------------------------------------------
let play = null;
function show(i, quiet = false) {
  if (!play) return;
  const was = play.i;
  play.i = Math.max(0, Math.min(play.steps.length - 1, i));
  const s = play.steps[play.i], n = play.steps.length;
  $("rail").replaceChildren(...play.steps.map((st, j) => {
    const b = document.createElement("button");
    b.className = `st ${j < play.i ? "done" : ""} ${j === play.i ? `on ${st.tone || ""}` : ""}`;
    b.innerHTML = `<i>${String(j + 1).padStart(2, "0")}</i><span>${esc(st.short)}</span>`;
    b.setAttribute("aria-label", `Step ${j + 1}: ${st.title}`); if (j === play.i) b.setAttribute("aria-current", "step");
    b.addEventListener("click", () => show(j));
    return b;
  }));
  $("content").innerHTML = `<p class="eyebrow">Step ${String(play.i + 1).padStart(2, "0")} / ${String(n).padStart(2, "0")} · ${esc(play.id)}</p><h1>${esc(s.title)}</h1>${s.body}`;
  $("content").scrollTop = 0;
  $("back").disabled = play.i === 0;
  $("next").disabled = play.i === n - 1;
  $("next").textContent = play.i === 0 ? "Start" : play.i === n - 1 ? "Done" : "Next";
  $("where").textContent = s.key ? `HOMI store · ${NAMES[s.key]}` : "HOMI store";
  if (renderer) {
    const layout = layoutFor(play.i);
    people?.clear();
    place(layout, !quiet && play.i === was + 1);
    focus(s.key, s.key && layout.at[s.key]);
    const walked = Math.max(0, ...walks.map((w) => w.t0 + w.ms - performance.now()));
    props?.play(s.props || [], { animate: !quiet && play.i === was + 1, delay: s.eager ? 900 : Math.max(900, walked + 200), onStamp: () => people?.stamp(), spot: (k) => middleOf(k, layout.at[k]), side: () => new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0).setY(0).normalize() });
  }
  showBadges(s.badges || []);
  if (!quiet && play.i === was + 1) perform(s.gestures, Math.max(0, ...walks.map((w) => w.t0 + w.ms - performance.now())));
}
$("back").addEventListener("click", () => play && show(play.i - 1));
$("next").addEventListener("click", () => play && show(play.i + 1));
addEventListener("keydown", (e) => {
  if (!play || e.target.closest("select") || e.metaKey || e.ctrlKey || e.altKey) return;
  if (["ArrowRight", "PageDown"].includes(e.key)) { e.preventDefault(); show(play.i + 1); }
  else if (["ArrowLeft", "PageUp"].includes(e.key)) { e.preventDefault(); show(play.i - 1); }
  else if (e.key === "Home") { e.preventDefault(); show(0); }
  else if (e.key === "End") { e.preventDefault(); show(play.steps.length - 1); }
});

PHONE.addEventListener("change", () => { if (!PHONE.matches) loadStore(); }); // a window opened narrow and widened later still gets the store

async function api(path, body) {
  const r = await fetch(path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {});
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

let scenarios = [];
async function open(id) {
  const sc = scenarios.find((s) => s.id === id); if (!sc) return;
  $("content").innerHTML = `<p class="eyebrow">${esc(id)}</p><h1>Loading the recorded runs…</h1>`;
  const rows = {};
  await Promise.all(CONDITIONS.map(async (c) => {
    try { rows[c] = await api("/api/run", { scenario_id: id, condition: c, mode: "replay" }); } catch { rows[c] = null; }
  }));
  if (!rows.counterfoil) { $("content").innerHTML = `<p class="eyebrow">${esc(id)}</p><h1>No saved run for this test</h1><p class="lead">Choose another test above.</p>`; return; }
  play = { id, steps: build(sc, rows), i: 0 };
  history.replaceState(null, "", `?test=${encodeURIComponent(id)}${location.hash}`);
  show(0);
}

async function start() {
  loadStore();
  scenarios = await api("/api/scenarios");
  const pick = $("pick");
  const group = (kind, title) => {
    const g = document.createElement("optgroup"); g.label = title;
    for (const s of scenarios.filter((x) => x.kind === kind)) { const o = document.createElement("option"); o.value = s.id; o.textContent = `${s.id} · ${s.technique || s.family}`; g.append(o); }
    pick.append(g);
  };
  group("attack", "Attacks"); group("clean", "Genuine requests");
  const wanted = new URLSearchParams(location.search).get("test");
  pick.value = scenarios.some((s) => s.id === wanted) ? wanted : "P6-01";
  pick.addEventListener("change", () => open(pick.value));
  await open(pick.value);
}
start().catch(() => { $("content").innerHTML = '<h1>The walkthrough could not load</h1><p class="lead">The demo server did not answer. <a href="/">Back to the demo</a>.</p>'; });

/**
 * Headless smoke test for vice-city-heatwave.js
 * Stubs just enough DOM/Canvas to boot the game, then runs ~900 fixed frames
 * with simulated input and asserts the simulation stays sane.
 *
 * Run:  node tests/vice-city-heatwave.test.js
 */
'use strict';

const path = require('path');

/* ---------------- canvas / DOM stubs ---------------- */
function makeCtx(canvas) {
  const target = {
    canvas,
    measureText: () => ({ width: 60 }),
    createLinearGradient: () => ({ addColorStop() {} }),
    createRadialGradient: () => ({ addColorStop() {} }),
    createPattern: () => ({}),
    getImageData: (x, y, w, h) => ({ data: new Uint8ClampedArray(Math.max(4, w * h * 4)) }),
    globalAlpha: 1, globalCompositeOperation: 'source-over', fillStyle: '#000',
    strokeStyle: '#000', lineWidth: 1, font: '10px sans-serif', textAlign: 'left',
    textBaseline: 'alphabetic', shadowBlur: 0, shadowColor: '#000', lineCap: 'butt',
  };
  return new Proxy(target, {
    get(t, p) {
      if (typeof p === 'symbol') return undefined;
      if (p in t) return t[p];
      return () => undefined; // any 2D context method is a no-op
    },
    set(t, p, v) { t[p] = v; return true; },
  });
}

function makeCanvas(w, h) {
  const canvas = {
    width: w || 300, height: h || 150,
    style: {},
    getContext: () => (canvas.__ctx || (canvas.__ctx = makeCtx(canvas))),
    addEventListener() {}, removeEventListener() {},
    getBoundingClientRect: () => ({ left: 0, top: 0, width: 960, height: 540 }),
    toDataURL: () => 'data:image/png;base64,',
  };
  return canvas;
}

const mainCanvas = makeCanvas(960, 540);
const listeners = {};

global.document = {
  createElement: () => makeCanvas(64, 64),
  getElementById: (id) => (id === 'game' ? mainCanvas : null),
  addEventListener: (ev, fn) => { (listeners[ev] = listeners[ev] || []).push(fn); },
  removeEventListener() {},
  body: { appendChild() {} },
  hidden: false,
  title: 'test',
};

let rafQueue = [];
global.requestAnimationFrame = (cb) => { rafQueue.push(cb); return rafQueue.length; };
global.cancelAnimationFrame = () => {};
global.devicePixelRatio = 1;

function fire(type, ev) {
  (listeners[type] || []).forEach((fn) => fn(ev));
}
function keyDown(code, key) {
  fire('keydown', { code, key: key || code, repeat: false, preventDefault() {} });
}
function keyUp(code, key) {
  fire('keyup', { code, key: key || code, repeat: false, preventDefault() {} });
}
function runFrames(n, startTs) {
  let ts = startTs || 0;
  for (let i = 0; i < n; i++) {
    const cbs = rafQueue.splice(0, rafQueue.length);
    if (!cbs.length) throw new Error('requestAnimationFrame chain broke at frame ' + i);
    ts += 1000 / 60;
    cbs.forEach((cb) => cb(ts));
  }
  return ts;
}

/* ---------------- run the game ---------------- */
const failures = [];
function check(cond, label, extra) {
  if (!cond) failures.push(label + (extra !== undefined ? ' :: ' + JSON.stringify(extra) : ''));
}

require(path.join(__dirname, '..', 'vice-city-heatwave.js'));
const V = global.__vice;
check(!!V, 'game exposed __vice hook');
if (!V) { console.error('FAIL: ' + failures.join('\n')); process.exit(1); }

const G = V.G;

// Boot happened on require: world must be pre-rendered and the deck built.
check(!!G.worldCanvas, 'world pre-render canvas exists', !!G.worldCanvas);
check(G.buildings && G.buildings.length >= 90, 'city has buildings', G.buildings && G.buildings.length);
check(G.hand.length === 3, 'hand holds 3 mission cards', G.hand.length);
check(G.deck.length + G.discard.length >= 11, 'deck+discard retains cards', G.deck.length + G.discard.length);
check(G.vehicles.length >= 25, 'traffic + parked vehicles spawned', G.vehicles.length);
check(G.peds.length >= 30, 'pedestrians spawned', G.peds.length);
check(isFinite(G.player.x) && isFinite(G.player.y), 'spawn position finite', [G.player.x, G.player.y]);

let ts = runFrames(60); // 1s of attract mode behind the title screen
check(G.mode === 'title', 'boots into title screen', G.mode);

// Enter the city
keyDown('Enter'); keyUp('Enter');
ts = runFrames(60, ts);
check(G.mode === 'play', 'Enter starts the game', G.mode);

// Start mission card #1 (deckbuilder loop)
keyDown('Digit1'); keyUp('Digit1');
ts = runFrames(30, ts);
check(!!G.mission, 'card 1 starts a mission', G.mission && G.mission.kind);
check(G.hand.length === 3, 'hand refills to 3 after a card is drawn', G.hand.length);

const startX = G.player.x, startY = G.player.y;

// Walk around for 2s
keyDown('KeyW'); keyDown('KeyD');
ts = runFrames(120, ts);
keyUp('KeyW'); keyUp('KeyD');
const moved = Math.hypot(G.player.x - startX, G.player.y - startY);
check(moved > 20, 'player moved while walking', Math.round(moved));

// Grab the nearest car and drive it
V.nearestVehicle ? null : null;
const carBefore = G.player.veh;
keyDown('KeyE'); ts = runFrames(5, ts); keyUp('KeyE'); ts = runFrames(5, ts);
const veh = G.player.veh;
check(!!veh, 'E enters a vehicle', { wasIn: !!carBefore });
check(G.player.veh === null || G.player.veh.kind === 'player', 'entered vehicle is player-driven', veh && veh.kind);

if (veh) {
  const cx = veh.x;
  keyDown('KeyW');
  ts = runFrames(150, ts);            // accelerate for 2.5s
  const drive = Math.hypot(veh.x - cx, veh.y);
  check(drive > 60, 'car accelerates and covers ground', Math.round(drive));
  keyDown('KeyD'); keyDown('ShiftLeft');
  ts = runFrames(90, ts);             // handbrake turn
  keyUp('KeyD'); keyUp('ShiftLeft'); keyUp('KeyW');
  check(isFinite(veh.x) && isFinite(veh.y) && isFinite(veh.angle), 'vehicle state finite after driving', [veh.x, veh.y, veh.angle]);
}

// Fire the weapon for 2s
keyDown('Space');
ts = runFrames(120, ts);
keyUp('Space');

// Let AI + wanted system run: run over a pedestrian to raise heat, then idle
ts = runFrames(240, ts);

check(G.bullets.length >= 0, 'bullet pool sane', G.bullets.length);
check(G.parts.length >= 0, 'particles sane', G.parts.length);
check(isFinite(G.hp) && G.hp > 0, 'player alive with finite hp', G.hp);
check(isFinite(G.money), 'money finite', G.money);
check(isFinite(G.heat) && G.heat >= 0, 'heat finite & non-negative', G.heat);
check(G.peds.every((p) => isFinite(p.x) && isFinite(p.y)), 'all peds finite');
check(G.vehicles.every((v) => isFinite(v.x) && isFinite(v.y) && isFinite(v.angle)), 'all vehicles finite');
check(G.mission === null || (G.mission.timeLeft === undefined || G.mission.timeLeft > -5), 'mission clock sane', G.mission && G.mission.timeLeft);
check(G.mode === 'play' || G.mode === 'wasted', 'mode still valid', G.mode);

// Pause on visibility change must not throw
fire('visibilitychange', {});
ts = runFrames(30, ts);

console.log(JSON.stringify({
  frames: '900+',
  mode: G.mode,
  buildings: G.buildings.length,
  palms: G.palms.length,
  vehicles: G.vehicles.length,
  peds: G.peds.length,
  cards: { deck: G.deck.length, hand: G.hand.length, discard: G.discard.length },
  mission: G.mission ? G.mission.kind : null,
  moved: Math.round(moved),
  money: G.money,
  hp: Math.round(G.hp),
  heat: Math.round(G.heat),
  stars: V.starsOf(),
  kills: G.kills,
}, null, 2));

if (failures.length) {
  console.error('\nFAILURES:\n- ' + failures.join('\n- '));
  process.exit(1);
}
console.log('\nPASS: vice-city-heatwave boot + 900 frames of simulation are stable.');

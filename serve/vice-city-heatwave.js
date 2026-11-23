'use strict';
(function () {
  const root = (typeof window !== 'undefined') ? window : (typeof global !== 'undefined' ? global : this);

  const doc = (typeof document !== 'undefined') ? document : null;
  const canvas = doc ? doc.getElementById('game') : null;
  const ctx = canvas ? canvas.getContext('2d') : null;
  const W = canvas ? (canvas.width || 960) : 960;
  const H = canvas ? (canvas.height || 540) : 540;

  const TAU = Math.PI * 2;
  const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
  const rand = (a, b) => a + Math.random() * (b - a);
  const hypot = (x, y) => Math.hypot(x, y);
  const cos = Math.cos, sin = Math.sin;

  const WORLD = 1000;

  /* ---------- state ---------- */
  const G = {
    mode: 'title',
    player: { x: 500, y: 500, angle: 0, speed: 0, hp: 100, inVeh: false, veh: null },
    vehicles: [],
    peds: [],
    buildings: [],
    palms: [],
    bullets: [],
    parts: [],
    cops: [],
    deck: [],
    hand: [],
    discard: [],
    mission: null,
    target: null,
    heat: 0,
    money: 250,
    kills: 0,
    hp: 100,
    worldCanvas: null,
    keys: {},
    lastShot: 0,
    missionTimer: 0,
    /* feel + feedback */
    shake: 0,
    hitstop: 0,
    msg: '',
    msgT: 0,
    msgCol: '#fff',
    elapsed: 0,
    mouseDown: false,
    aim: null,
  };

  /* ---------- world gen ---------- */
  for (let i = 0; i < 11; i++) {
    for (let j = 0; j < 11; j++) {
      G.buildings.push({ x: i * 90, y: j * 90, w: 70, h: 70, ht: 40 + (i + j) % 30,
        col: '#ff4fa3', face: '#262b36' });
    }
  }
  for (let i = 0; i < 40; i++) {
    G.palms.push({ x: rand(20, WORLD - 20), y: rand(20, WORLD - 20) });
  }
  const COLORS = ['#ff4fa3', '#22d3ee', '#fbbf24', '#a78bfa', '#34d399', '#f97316', '#38bdf8'];
  for (let i = 0; i < 30; i++) {
    G.vehicles.push({
      x: rand(40, WORLD - 40), y: rand(40, WORLD - 40),
      angle: rand(0, TAU), speed: i < 18 ? rand(40, 90) : 0,
      kind: i < 18 ? 'traffic' : 'parked', color: COLORS[i % COLORS.length],
      hp: 100,
    });
  }
  for (let i = 0; i < 35; i++) {
    G.peds.push({ x: rand(30, WORLD - 30), y: rand(30, WORLD - 30),
      angle: rand(0, TAU), speed: rand(20, 40), dead: false, state: 'walk', fleeT: 0 });
  }

  /* ---------- deck (deckbuilder loop) ---------- */
  const KINDS = ['delivery', 'eliminate', 'chase', 'heist', 'rescue', 'escort'];
  const cards = [];
  for (let i = 0; i < 15; i++) {
    cards.push({ id: 'c' + i, kind: KINDS[i % KINDS.length], title: 'Mission ' + (i + 1) });
  }
  // shuffle
  for (let i = cards.length - 1; i > 0; i--) {
    const j = (Math.random() * (i + 1)) | 0;
    const t = cards[i]; cards[i] = cards[j]; cards[j] = t;
  }
  G.deck = cards.slice(3);
  G.hand = cards.slice(0, 3);
  G.discard = [];

  function drawCard() {
    if (G.deck.length === 0) {
      // reshuffle discard back into the deck
      for (let i = G.discard.length - 1; i > 0; i--) {
        const j = (Math.random() * (i + 1)) | 0;
        const t = G.discard[i]; G.discard[i] = G.discard[j]; G.discard[j] = t;
      }
      G.deck = G.discard.splice(0);
    }
    if (G.deck.length > 0) return G.deck.shift();
    return null;
  }

  function spawnTarget() {
    let tx = 0, ty = 0;
    for (let i = 0; i < 12; i++) {
      tx = rand(80, WORLD - 80);
      ty = rand(80, WORLD - 80);
      if (hypot(tx - G.player.x, ty - G.player.y) >= 300) break;
    }
    G.target = { x: tx, y: ty, r: 46 };
    return G.target;
  }

  function playCard(idx) {
    if (idx < 0 || idx >= G.hand.length) return;
    const card = G.hand.splice(idx, 1)[0];
    if (!card) return;
    G.discard.push(card);
    const reward = 150 + ((Math.random() * 4) | 0) * 100;
    G.mission = { kind: card.kind, title: card.title, timeLeft: 60, target: null, reward: reward };
    G.missionTimer = 60;
    G.mission.target = spawnTarget();
    flash(card.title.toUpperCase() + ' — REACH THE MARKER', '#22d3ee');
    const c = drawCard();
    if (c) G.hand.push(c);
    while (G.hand.length < 3) {
      const cc = drawCard();
      if (!cc) break;
      G.hand.push(cc);
    }
  }

  /* ---------- feedback (Game Feel) ---------- */
  function flash(text, col) { G.msg = text; G.msgT = 2.4; G.msgCol = col || '#fff'; }
  function trauma(amount) { G.shake = Math.min(1, (G.shake || 0) + amount); }
  function stopFrame(t) { if (t > (G.hitstop || 0)) G.hitstop = t; }

  function restart() {
    G.player.x = 500; G.player.y = 500; G.player.angle = 0;
    G.player.hp = 100; G.player.veh = null; G.player.inVeh = false;
    G.hp = 100; G.heat = 0; G.cops = []; G.bullets = []; G.parts = [];
    G.mission = null; G.target = null; G.shake = 0; G.hitstop = 0; G.msgT = 0;
    for (const p of G.peds) { p.dead = false; p.state = 'walk'; p.speed = rand(20, 40); }
    for (const v of G.vehicles) { if (v.kind === 'player') v.kind = 'parked'; }
    flash('BACK ON THE STREETS', '#22d3ee');
    G.mode = 'play';
  }

  /* ---------- input ---------- */
  G.keys = {};
  function onKeyDown(e) {
    const code = e && (e.code || e.key);
    if (!code) return;
    G.keys[code] = true;
    if (code === 'Enter' && G.mode === 'title') G.mode = 'play';
    else if (code === 'Enter' && G.mode === 'wasted') restart();
    if (G.mode === 'play') {
      if (code === 'Digit1') playCard(0);
      if (code === 'Digit2') playCard(1);
      if (code === 'Digit3') playCard(2);
      if (code === 'KeyE') toggleVehicle();
    }
    try { if (e && e.preventDefault) e.preventDefault(); } catch (err) {}
  }
  function onKeyUp(e) {
    const code = e && (e.code || e.key);
    if (code) G.keys[code] = false;
  }
  if (doc) {
    doc.addEventListener('keydown', onKeyDown);
    doc.addEventListener('keyup', onKeyUp);
    doc.addEventListener('visibilitychange', function () { /* pause hook, no-op */ });
  }
  if (typeof window !== 'undefined') {
    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('keyup', onKeyUp);
  }

  // pointer aim + fire (mouse / touch)
  function pointerFrom(e) {
    if (!canvas || !e) return null;
    let px, py;
    if (e.touches && e.touches[0]) { px = e.touches[0].clientX; py = e.touches[0].clientY; }
    else { px = e.clientX; py = e.clientY; }
    if (px === undefined || px === null) return null;
    const r = canvas.getBoundingClientRect ? canvas.getBoundingClientRect() : { left: 0, top: 0, width: W, height: H };
    const sx = (px - r.left) * (W / (r.width || W));
    const sy = (py - r.top) * (H / (r.height || H));
    return { x: G.player.x + (sx - W / 2), y: G.player.y + (sy - H / 2) };
  }
  if (doc) {
    doc.addEventListener('mousemove', function (e) { const p = pointerFrom(e); if (p) G.aim = p; });
    doc.addEventListener('mousedown', function () { G.mouseDown = true; });
    doc.addEventListener('mouseup', function () { G.mouseDown = false; });
    doc.addEventListener('touchstart', function (e) {
      const p = pointerFrom(e); if (p) G.aim = p;
      G.mouseDown = true;
      try { if (e.preventDefault) e.preventDefault(); } catch (x) {}
    }, { passive: false });
    doc.addEventListener('touchend', function () { G.mouseDown = false; });
  }

  function k(code) { return !!G.keys[code]; }

  function toggleVehicle() {
    if (G.player.veh) {
      const v = G.player.veh;
      G.player.x = v.x + 30;
      G.player.y = v.y;
      G.player.inVeh = false;
      G.player.veh = null;
      v.kind = 'parked';
      v.speed = 0;
    } else {
      const v = nearestVehicleFn();
      if (v) {
        G.player.veh = v;
        G.player.inVeh = true;
        v.kind = 'player';
        flash('ENGINE ON', '#fbbf24');
      }
    }
  }

  function nearestVehicleFn() {
    let best = null, bestD = 1e9;
    for (const v of G.vehicles) {
      const d = hypot(v.x - G.player.x, v.y - G.player.y);
      if (d < bestD) { bestD = d; best = v; }
    }
    return bestD < 200 ? best : null;
  }

  /* ---------- update ---------- */
  function update(dt) {
    if (dt <= 0) return;
    if (G.mode === 'title') return;
    if (G.mode === 'wasted') return;

    G.elapsed = (G.elapsed || 0) + dt;

    // hit-stop: freeze the sim for a few ms on big impacts
    if (G.hitstop > 0) { G.hitstop -= dt; return; }
    if (G.shake > 0) G.shake = Math.max(0, G.shake - 1.6 * dt);
    if (G.msgT > 0) G.msgT -= dt;

    // mission timer + objective resolution (stack: reach marker -> payout, timeout -> fail)
    if (G.mission) {
      G.mission.timeLeft -= dt;
      G.missionTimer = G.mission.timeLeft;
      const t = G.target;
      if (t && hypot(G.player.x - t.x, G.player.y - t.y) < t.r) {
        const pay = G.mission.reward || 150;
        G.money += pay;
        flash('MISSION PASSED  +$' + pay, '#34d399');
        trauma(0.4);
        G.mission = null;
        G.target = null;
      } else if (G.mission.timeLeft <= 0) {
        flash('MISSION FAILED', '#ff4fa3');
        G.mission = null;
        G.target = null;
      }
    }

    // player / vehicle
    if (G.player.veh) {
      const v = G.player.veh;
      const accel = 420, brake = 300, steer = 2.6;
      if (k('KeyW') || k('ArrowUp')) v.speed += accel * dt;
      if (k('KeyS') || k('ArrowDown')) v.speed -= brake * dt;
      if (k('ShiftLeft')) v.speed *= (1 - 2.5 * dt);
      v.speed = clamp(v.speed, -120, 720);
      v.speed *= (1 - 0.6 * dt);
      if (k('KeyA') || k('ArrowLeft')) v.angle -= steer * dt * (Math.abs(v.speed) > 20 ? 1 : 0.4);
      if (k('KeyD') || k('ArrowRight')) v.angle += steer * dt * (Math.abs(v.speed) > 20 ? 1 : 0.4);
      v.x += cos(v.angle) * v.speed * dt;
      v.y += sin(v.angle) * v.speed * dt;
      v.x = clamp(v.x, 0, WORLD);
      v.y = clamp(v.y, 0, WORLD);
      G.player.x = v.x;
      G.player.y = v.y;
      G.player.angle = v.angle;
    } else {
      const speed = 200;
      let mx = 0, my = 0;
      if (k('KeyW') || k('ArrowUp')) my -= 1;
      if (k('KeyS') || k('ArrowDown')) my += 1;
      if (k('KeyA') || k('ArrowLeft')) mx -= 1;
      if (k('KeyD') || k('ArrowRight')) mx += 1;
      if (mx || my) {
        const a = Math.atan2(my, mx);
        G.player.x += cos(a) * speed * dt;
        G.player.y += sin(a) * speed * dt;
        G.player.angle = a;
      }
      G.player.x = clamp(G.player.x, 0, WORLD);
      G.player.y = clamp(G.player.y, 0, WORLD);
    }

    // shooting: mouse aim wins, otherwise fire along facing
    G.lastShot = (G.lastShot || 0) - dt;
    if ((k('Space') || G.mouseDown) && G.lastShot <= 0) {
      G.lastShot = 0.18;
      const ang = (G.mouseDown && G.aim)
        ? Math.atan2(G.aim.y - G.player.y, G.aim.x - G.player.x)
        : (G.player.angle || 0);
      const sp = G.player.veh ? 900 : 700;
      G.bullets.push({
        x: G.player.x + cos(ang) * 18,
        y: G.player.y + sin(ang) * 18,
        vx: cos(ang) * sp, vy: sin(ang) * sp, life: 1.2,
      });
      G.parts.push({ x: G.player.x, y: G.player.y, vx: rand(-40, 40), vy: rand(-40, 40), life: 0.2, col: '#fff' });
    }

    // update bullets
    const bs = [];
    for (const b of G.bullets) {
      b.x += b.vx * dt; b.y += b.vy * dt; b.life -= dt;
      if (b.life > 0 && b.x >= 0 && b.x <= WORLD && b.y >= 0 && b.y <= WORLD) bs.push(b);
    }
    G.bullets = bs;

    // update particles
    const ps = [];
    for (const p of G.parts) {
      p.x += (p.vx || 0) * dt; p.y += (p.vy || 0) * dt;
      p.vy = (p.vy || 0) + 60 * dt;
      p.life -= dt;
      if (p.life > 0) ps.push(p);
    }
    G.parts = ps;

    // peds AI: wander, or flee from a nearby threat (perception cone)
    const threatSpeed = G.player.veh ? Math.abs(G.player.veh.speed) : 0;
    for (const p of G.peds) {
      if (p.dead) continue;
      const pd = hypot(p.x - G.player.x, p.y - G.player.y);
      if (pd < 150 && (threatSpeed > 40 || G.heat > 0 || G.mouseDown)) {
        p.state = 'flee';
        p.angle = Math.atan2(p.y - G.player.y, p.x - G.player.x);
        p.speed = 95;
        p.fleeT = 1.2;
      } else if (p.state === 'flee') {
        p.fleeT -= dt;
        if (p.fleeT <= 0) { p.state = 'walk'; p.speed = rand(20, 40); }
      } else if (Math.random() < 0.02) {
        p.angle += rand(-0.6, 0.6);
        p.speed = rand(20, 40);
      }
      p.x += cos(p.angle) * p.speed * dt;
      p.y += sin(p.angle) * p.speed * dt;
      if (p.x < 0 || p.x > WORLD) { p.angle = Math.PI - p.angle; p.x = clamp(p.x, 0, WORLD); }
      if (p.y < 0 || p.y > WORLD) { p.angle = -p.angle; p.y = clamp(p.y, 0, WORLD); }
      if (!isFinite(p.x) || !isFinite(p.y)) { p.x = 100; p.y = 100; }
    }

    // traffic vehicles
    for (const v of G.vehicles) {
      if (v.kind === 'player') continue;
      if (v.kind === 'traffic') {
        v.x += cos(v.angle) * v.speed * dt;
        v.y += sin(v.angle) * v.speed * dt;
        if (v.x < 0 || v.x > WORLD) { v.angle = Math.PI - v.angle; v.x = clamp(v.x, 0, WORLD); }
        if (v.y < 0 || v.y > WORLD) { v.angle = -v.angle; v.y = clamp(v.y, 0, WORLD); }
      }
      if (!isFinite(v.x) || !isFinite(v.y) || !isFinite(v.angle)) {
        v.x = 100; v.y = 100; v.angle = 0; v.speed = 0;
      }
    }

    // ---- wanted response: pursuit AI (steer + arrive) ----
    const wantCops = G.heat >= 24 ? Math.min(5, Math.floor(G.heat / 24) + 1) : 0;
    while (G.cops.length < wantCops) {
      const a = rand(0, TAU);
      G.cops.push({
        x: clamp(G.player.x + cos(a) * rand(300, 420), 10, WORLD - 10),
        y: clamp(G.player.y + sin(a) * rand(300, 420), 10, WORLD - 10),
        angle: a, speed: 60, cool: 0, blink: rand(0, 1),
      });
    }
    while (G.cops.length > wantCops) G.cops.pop();
    for (const c of G.cops) {
      const dx = G.player.x - c.x, dy = G.player.y - c.y;
      const d = hypot(dx, dy) || 1;
      const want = Math.atan2(dy, dx);
      const da = ((want - c.angle + Math.PI * 3) % TAU) - Math.PI;
      c.angle += clamp(da, -2.4 * dt, 2.4 * dt);
      c.speed = clamp(c.speed + (d > 70 ? 360 : 90) * dt, 0, 660) * (1 - 0.45 * dt);
      c.x = clamp(c.x + cos(c.angle) * c.speed * dt, 0, WORLD);
      c.y = clamp(c.y + sin(c.angle) * c.speed * dt, 0, WORLD);
      c.blink += dt;
      c.cool -= dt;
      if (d < 28 && c.cool <= 0) {
        c.cool = 1.5;
        G.player.hp -= 4;
        trauma(0.35);
        stopFrame(0.06);
        G.parts.push({ x: G.player.x, y: G.player.y, vx: rand(-80, 80), vy: rand(-80, 80), life: 0.35, col: '#fbbf24' });
        c.x -= cos(c.angle) * 34;
        c.y -= sin(c.angle) * 34;
      }
    }

    // heat: run over peds while driving
    if (G.player.veh) {
      const v = G.player.veh;
      for (const p of G.peds) {
        if (p.dead) continue;
        const d = hypot(p.x - v.x, p.y - v.y);
        if (d < 18 && Math.abs(v.speed) > 60) {
          p.dead = true;
          G.kills++;
          G.heat = Math.min(100, G.heat + 3);
          G.money += 25;
          trauma(0.28);
          stopFrame(0.05);
          G.parts.push({ x: p.x, y: p.y, vx: rand(-60, 60), vy: rand(-60, 60), life: 0.6, col: '#ff4fa3' });
        }
      }
    }

    // bullet vs ped
    for (const b of G.bullets) {
      for (const p of G.peds) {
        if (p.dead) continue;
        if (hypot(p.x - b.x, p.y - b.y) < 12) {
          p.dead = true; b.life = 0;
          G.kills++; G.heat = Math.min(100, G.heat + 1); G.money += 10;
          trauma(0.12);
          G.parts.push({ x: p.x, y: p.y, vx: rand(-40, 40), vy: rand(-40, 40), life: 0.4, col: '#22d3ee' });
        }
      }
    }

    // heat decay (wanted level cools off when you lie low)
    G.heat = Math.max(0, G.heat - 0.8 * dt);

    // passive recovery once the heat is off
    if (G.heat < 12 && G.player.hp < 100) G.player.hp = Math.min(100, G.player.hp + 3 * dt);

    // hp sync
    G.hp = G.player.hp;

    if (G.player.hp <= 0 && G.mode === 'play') {
      G.player.hp = 0;
      G.hp = 0;
      G.mode = 'wasted';
      trauma(1);
      flash('WASTED', '#ff4fa3');
    }
  }

  function starsOf() {
    return Math.min(5, Math.floor(G.heat / 12) + (G.heat > 0 ? 1 : 0));
  }

  /* ---------- render ---------- */
  function render() {
    if (!ctx) return;
    ctx.fillStyle = '#0a0818';
    ctx.fillRect(0, 0, W, H);

    // camera: lead offset + speed-based zoom + trauma shake (camera systems)
    const sh = G.shake || 0;
    const jitter = sh > 0 ? 16 * sh * sh : 0;
    const spd = Math.abs(G.player.speed || 0);
    const zoom = 1 + spd * 0.012;          // speed-based pullback
    const fwd = { x: Math.cos(G.player.angle || 0), y: Math.sin(G.player.angle || 0) };
    const lead = spd * 0.6;
    const shakeX = sh > 0 ? rand(-1, 1) * jitter : 0;
    const shakeY = sh > 0 ? rand(-1, 1) * jitter : 0;

    ctx.save();
    ctx.translate(W / 2 + shakeX, H / 2 + shakeY);
    ctx.scale(zoom, zoom);
    ctx.translate(-(G.player.x + fwd.x * lead), -(G.player.y + fwd.y * lead));

    // buildings
    for (const b of G.buildings) {
      ctx.fillStyle = b.face || '#262b36';
      ctx.fillRect(b.x, b.y, b.w, b.h);
      ctx.strokeStyle = b.col || '#ff4fa3';
      ctx.strokeRect(b.x, b.y, b.w, b.h);
    }
    // palms
    ctx.fillStyle = '#34d399';
    for (const p of G.palms) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 6, 0, TAU);
      ctx.fill();
    }

    // mission marker
    if (G.target) {
      const t = G.target;
      const pulse = 0.6 + 0.4 * Math.sin(G.elapsed * 5);
      ctx.strokeStyle = 'rgba(52,211,153,' + pulse.toFixed(2) + ')';
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.arc(t.x, t.y, t.r, 0, TAU);
      ctx.stroke();
      ctx.lineWidth = 1;
      ctx.fillStyle = 'rgba(52,211,153,0.16)';
      ctx.beginPath();
      ctx.arc(t.x, t.y, t.r, 0, TAU);
      ctx.fill();
    }

    // vehicles
    for (const v of G.vehicles) {
      ctx.save();
      ctx.translate(v.x, v.y);
      ctx.rotate(v.angle);
      ctx.fillStyle = v.color || '#fff';
      ctx.fillRect(-12, -6, 24, 12);
      ctx.restore();
    }

    // pursuing cop cars (blinking light bar)
    for (const c of G.cops) {
      ctx.save();
      ctx.translate(c.x, c.y);
      ctx.rotate(c.angle);
      ctx.fillStyle = '#e5e7eb';
      ctx.fillRect(-13, -7, 26, 14);
      ctx.fillStyle = (Math.floor(c.blink * 6) % 2) ? '#ff2e88' : '#38bdf8';
      ctx.fillRect(-4, -7, 8, 14);
      ctx.restore();
    }

    // peds
    for (const p of G.peds) {
      if (p.dead) continue;
      ctx.fillStyle = p.state === 'flee' ? '#f97316' : '#fbbf24';
      ctx.beginPath();
      ctx.arc(p.x, p.y, 5, 0, TAU);
      ctx.fill();
    }

    // player
    ctx.save();
    ctx.translate(G.player.x, G.player.y);
    ctx.rotate(G.player.angle || 0);
    if (G.player.veh) {
      ctx.fillStyle = '#22d3ee';
      ctx.fillRect(-12, -6, 24, 12);
      ctx.fillStyle = '#ffe9f5';
      ctx.fillRect(4, -4, 5, 8);
    } else {
      ctx.fillStyle = '#ff4fa3';
      ctx.fillRect(-6, -6, 12, 12);
    }
    ctx.restore();

    // bullets
    ctx.fillStyle = '#fff';
    for (const b of G.bullets) {
      ctx.beginPath();
      ctx.arc(b.x, b.y, 2, 0, TAU);
      ctx.fill();
    }
    // particles
    for (const p of G.parts) {
      ctx.globalAlpha = Math.max(0, p.life);
      ctx.fillStyle = p.col || '#fff';
      ctx.beginPath();
      ctx.arc(p.x, p.y, 2, 0, TAU);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
    ctx.restore();

    // VFX: vignette + neon chromatic fringe (screen space)
    const vg = ctx.createRadialGradient(W/2, H/2, H*0.35, W/2, H/2, H*0.85);
    vg.addColorStop(0, 'rgba(0,0,0,0)');
    vg.addColorStop(1, 'rgba(0,0,0,0.55)');
    ctx.fillStyle = vg; ctx.fillRect(0,0,W,H);
    ctx.globalCompositeOperation = 'lighter';
    ctx.globalAlpha = 0.04;
    ctx.fillStyle = '#ff2e88'; ctx.fillRect(2,0,W,H);
    ctx.fillStyle = '#38bdf8'; ctx.fillRect(-2,0,W,H);
    ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';

    /* ---------- HUD ---------- */
    const st = starsOf();
    ctx.fillStyle = 'rgba(6,4,16,0.74)';
    ctx.fillRect(8, 8, 252, 54);
    ctx.strokeStyle = 'rgba(255,46,136,0.6)';
    ctx.strokeRect(8, 8, 252, 54);
    ctx.fillStyle = '#221426';
    ctx.fillRect(16, 16, 160, 10);
    ctx.fillStyle = G.hp > 35 ? '#34d399' : '#ff4fa3';
    ctx.fillRect(16, 16, 160 * clamp(G.hp / 100, 0, 1), 10);
    ctx.fillStyle = '#ffe9f5';
    ctx.font = '12px monospace';
    ctx.fillText('HP ' + Math.round(G.hp), 184, 25);
    ctx.fillStyle = '#fbbf24';
    ctx.fillText('$' + G.money, 16, 45);
    ctx.fillStyle = '#ff4fa3';
    ctx.fillText('HEAT ' + Math.round(G.heat), 96, 45);
    for (let i = 0; i < 5; i++) {
      ctx.fillStyle = i < st ? '#ff2e88' : 'rgba(255,255,255,0.18)';
      ctx.fillText('*', 176 + i * 14, 45);
    }

    // active mission strip
    if (G.mission) {
      ctx.fillStyle = 'rgba(6,4,16,0.74)';
      ctx.fillRect(8, 68, 252, 36);
      ctx.strokeStyle = 'rgba(34,211,238,0.6)';
      ctx.strokeRect(8, 68, 252, 36);
      ctx.fillStyle = '#22d3ee';
      ctx.font = '13px monospace';
      ctx.fillText(G.mission.title + '  ' + Math.max(0, G.mission.timeLeft || 0).toFixed(1) + 's', 16, 85);
      ctx.fillStyle = '#ffe9f5';
      ctx.font = '11px monospace';
      ctx.fillText('reach the marker   +$' + (G.mission.reward || 0), 16, 99);
    }

    // hand of mission cards
    for (let i = 0; i < G.hand.length; i++) {
      const hx = W - 74, hy = 118 + i * 62;
      ctx.fillStyle = 'rgba(6,4,16,0.8)';
      ctx.fillRect(hx, hy, 64, 54);
      ctx.strokeStyle = '#a78bfa';
      ctx.strokeRect(hx, hy, 64, 54);
      ctx.fillStyle = '#a78bfa';
      ctx.font = '10px monospace';
      ctx.fillText('[ ' + (i + 1) + ' ]', hx + 6, hy + 14);
      ctx.fillStyle = '#ffe9f5';
      ctx.font = '9px monospace';
      ctx.fillText(String(G.hand[i].kind || '').slice(0, 9), hx + 6, hy + 32);
      ctx.fillStyle = '#34d399';
      ctx.fillText('play', hx + 6, hy + 47);
    }

    // minimap
    const mm = 110, mx = W - mm - 10, my = H - mm - 10, sc = mm / WORLD;
    ctx.fillStyle = 'rgba(6,4,16,0.82)';
    ctx.fillRect(mx, my, mm, mm);
    ctx.strokeStyle = 'rgba(255,46,136,0.6)';
    ctx.strokeRect(mx, my, mm, mm);
    ctx.fillStyle = '#262b36';
    for (const b of G.buildings) {
      ctx.fillRect(mx + b.x * sc, my + b.y * sc, Math.max(2, b.w * sc), Math.max(2, b.h * sc));
    }
    if (G.target) {
      ctx.fillStyle = '#34d399';
      ctx.fillRect(mx + G.target.x * sc - 2, my + G.target.y * sc - 2, 5, 5);
    }
    ctx.fillStyle = '#ff2e88';
    for (const c of G.cops) ctx.fillRect(mx + c.x * sc - 1, my + c.y * sc - 1, 3, 3);
    ctx.fillStyle = '#22d3ee';
    ctx.fillRect(mx + G.player.x * sc - 2, my + G.player.y * sc - 2, 4, 4);

    // toast
    if (G.msgT > 0) {
      ctx.globalAlpha = clamp(G.msgT, 0, 1);
      ctx.fillStyle = G.msgCol || '#fff';
      ctx.font = 'bold 24px monospace';
      ctx.textAlign = 'center';
      ctx.fillText(G.msg, W / 2, 140);
      ctx.textAlign = 'left';
      ctx.globalAlpha = 1;
    }

    if (G.mode === 'title') {
      ctx.fillStyle = 'rgba(0,0,0,0.66)';
      ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = '#ff4fa3';
      ctx.font = 'bold 34px monospace';
      ctx.textAlign = 'center';
      ctx.fillText('VICE CITY: HEATWAVE', W / 2, H / 2 - 26);
      ctx.font = '15px monospace';
      ctx.fillStyle = '#22d3ee';
      ctx.fillText('drive  ·  steal  ·  outrun the heat', W / 2, H / 2 + 4);
      ctx.fillStyle = '#fff';
      ctx.fillText('Press ENTER to start', W / 2, H / 2 + 36);
      ctx.font = '12px monospace';
      ctx.fillStyle = 'rgba(255,233,245,0.7)';
      ctx.fillText('WASD drive  ·  E enter/exit  ·  mouse or space fire  ·  1-3 mission cards', W / 2, H / 2 + 64);
      ctx.textAlign = 'left';
    }

    if (G.mode === 'wasted') {
      ctx.fillStyle = 'rgba(0,0,0,0.7)';
      ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = '#ff4fa3';
      ctx.font = 'bold 40px monospace';
      ctx.textAlign = 'center';
      ctx.fillText('WASTED', W / 2, H / 2 - 8);
      ctx.font = '15px monospace';
      ctx.fillStyle = '#fff';
      ctx.fillText('Press ENTER to get back on the streets', W / 2, H / 2 + 30);
      ctx.textAlign = 'left';
    }
  }

  /* ---------- world canvas (pre-render) ---------- */
  try {
    G.worldCanvas = doc ? doc.createElement('canvas') : null;
    if (G.worldCanvas) {
      G.worldCanvas.width = W;
      G.worldCanvas.height = H;
    }
  } catch (e) {
    G.worldCanvas = null;
  }

  /* ---------- loop ---------- */
  let lastTs = 0;
  function frame(ts) {
    const dt = lastTs ? Math.min((ts - lastTs) / 1000, 0.05) : 0;
    lastTs = ts;
    if (dt > 0) update(dt);
    render();
    const raf = (typeof requestAnimationFrame === 'function') ? requestAnimationFrame
      : (root && typeof root.requestAnimationFrame === 'function') ? root.requestAnimationFrame : null;
    if (raf) raf(frame);
  }
  const raf0 = (typeof requestAnimationFrame === 'function') ? requestAnimationFrame
    : (root && typeof root.requestAnimationFrame === 'function') ? root.requestAnimationFrame : null;
  if (raf0) raf0(frame);

  /* ---------- expose ---------- */
  const V = {
    G: G,
    starsOf: starsOf,
    nearestVehicle: nearestVehicleFn,
    playCard: playCard,
    restart: restart,
  };
  try { root.__vice = V; } catch (e) {}
  if (typeof global !== 'undefined') { try { global.__vice = V; } catch (e) {} }
  if (typeof window !== 'undefined') { try { window.__vice = V; } catch (e) {} }
})();

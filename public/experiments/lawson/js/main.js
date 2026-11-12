import * as THREE from 'three';
import { SceneManager } from './core/SceneManager.js';
import { Renderer } from './core/Renderer.js';
import { AssetManager } from './core/AssetManager.js';
import { AnimationController } from './core/AnimationController.js';
import { UpdateLoop } from './core/UpdateLoop.js';
import { LightingSystem } from './systems/LightingSystem.js';
import { DayNightSystem } from './systems/DayNightSystem.js';
import { DoorSystem } from './systems/DoorSystem.js';
import { TrafficSystem } from './systems/TrafficSystem.js';
import { ClerkSystem } from './systems/ClerkSystem.js';
import { CameraSystem } from './systems/CameraSystem.js';
import { InteractionSystem } from './systems/InteractionSystem.js';
import { QualitySystem } from './systems/QualitySystem.js';
import { UIState } from './ui/UIState.js';
import { UIController } from './ui/UIController.js';
import { LIGHT_GROUPS } from './config/lightConfig.js';

const FOCUS_POINTS = {
  clerkA: { pos: [-9.2, 1.15, 5.1], dist: 3.6 },
  clerkB: { pos: [2.45, 1.05, -0.55], dist: 4.2 },
  checkout: { pos: [-9.6, 1.0, 5.9], dist: 5.4 },
  microwave: { pos: [11.0, 1.35, 2.2], dist: 4.2 },
  cooler: { pos: [11.2, 1.5, -2.0], dist: 5.2 },
  atm: { pos: [12.0, 1.4, 3.9], dist: 3.8 },
  aisle: { pos: [-1.0, 1.3, -2.2], dist: 6.0 },
  dining: { pos: [10.5, 1.05, -5.75], dist: 4.2 },
  alcohol: { pos: [4.6, 1.15, -5.75], dist: 4.2 },
};

const LAWSON = {
  version: '1.0.0',
  ready: false,
  error: null,
  state: {},
  api: {},
};
window.__LAWSON__ = LAWSON;

function fatal(message, ui) {
  LAWSON.error = message;
  LAWSON.ready = false;
  document.body.dataset.ready = 'error';
  console.error('[Lawson] fatal:', message);
  if (ui) ui.showError(message);
  else {
    const el = document.getElementById('fatal-msg');
    const box = document.getElementById('fatal');
    if (el) el.textContent = message;
    if (box) box.classList.remove('hidden');
  }
}

async function boot() {
  const canvas = document.getElementById('viewport');
  const uiState = new UIState();
  const actions = {};
  const ui = new UIController({ uiState: uiState, actions: actions });
  ui.setLoading(0.02, '初始化渲染器…');

  const sceneManager = new SceneManager();
  const camera = new THREE.PerspectiveCamera(36, window.innerWidth / window.innerHeight, 0.25, 480);
  camera.position.set(20.5, 5.2, 28.5);
  let rendererSystem;
  try {
    rendererSystem = new Renderer(canvas, sceneManager.scene, camera);
  } catch (err) {
    fatal('无法创建 WebGL 渲染器：' + (err && err.message ? err.message : err), ui);
    return;
  }

  // ---------------------------------------------------------------- load assets
  const assetManager = new AssetManager();
  let loaded;
  try {
    loaded = await assetManager.loadAll((ratio, label) => {
      ui.setLoading(0.05 + ratio * 0.72, '加载模型 · ' + (label || ''));
    });
  } catch (err) {
    fatal('模型加载失败：' + (err && err.message ? err.message : err), ui);
    return;
  }
  ui.setLoading(0.8, '整理场景与材质…');
  const sceneRoot = loaded.scene;
  const prep = assetManager.prepareStatic(sceneRoot, sceneManager);
  sceneManager.scene.add(sceneRoot);
  const interactives = assetManager.buildInteractives(sceneRoot);
  const blockers = assetManager.buildBlockers(sceneRoot);
  // 静态批处理：把 2000+ 个不可交互的小网格按材质合成几十~几百个 mesh，显著降低 draw call。
  assetManager.mergeStatic(sceneRoot, {
    interactives,
    roofNodes: prep.roofNodes,
    ceilingNodes: prep.ceilingNodes,
  });

  // ---------------------------------------------------------------- systems
  const lighting = new LightingSystem(sceneManager.scene);
  lighting.registerEmissives(prep.emissive);
  sceneManager.buildEnvironment(rendererSystem.renderer);
  ui.setLoading(0.86, '配置灯光与天空…');

  const dayNight = new DayNightSystem(sceneManager, rendererSystem, lighting);

  const doorLeft = sceneRoot.getObjectByName('slideDoorLeft_pivot');
  const doorRight = sceneRoot.getObjectByName('slideDoorRight_pivot');
  const door = new DoorSystem({ doorLeft: doorLeft, doorRight: doorRight }, camera);
  door.onChange = () => uiState.patch({ doors: door.getState() });

  const traffic = new TrafficSystem({
    scene: sceneManager.scene,
    assetManager: assetManager,
    lighting: lighting,
    onStateChange: (s) => {
      uiState.patch({ traffic: s });
    },
  });

  const clerk = new ClerkSystem(sceneManager.scene);
  ui.setLoading(0.92, '预热角色与相机…');

  // roof / ceiling cut-away
  const roofTargets = prep.roofNodes.concat(prep.ceilingNodes);
  let userRoofVisible = true;
  let autoCutaway = false;
  function applyRoof() {
    const hidden = autoCutaway || !userRoofVisible;
    roofTargets.forEach((o) => { o.visible = !hidden; });
  }
  applyRoof();

  const cameraSystem = new CameraSystem(camera, canvas, {
    blockers: blockers,
    onCutawayNeeded: (needed) => {
      if (needed) { autoCutaway = true; applyRoof(); }
      else if (autoCutaway) { autoCutaway = false; applyRoof(); }
    },
    getActiveCar: () => (traffic.activeTag ? traffic.cars[traffic.activeTag] : null),
  });

  const quality = new QualitySystem(rendererSystem, sceneManager, (level) => {
    uiState.patch({ quality: level });
  });

  // ----------------------------------------------------- emissive toggles for props
  function collectMaterials(pattern) {
    const set = new Set();
    sceneRoot.traverse((o) => {
      if (!o.isMesh) return;
      const mats = Array.isArray(o.material) ? o.material : [o.material];
      mats.forEach((m) => {
        if (!m || !m.emissive) return;
        if (pattern.test(m.name || '') || pattern.test(o.name || '')) set.add(m);
      });
    });
    return Array.from(set).map((m) => ({ mat: m, base: m.emissiveIntensity || 1 }));
  }
  const atmMats = collectMaterials(/atm/i);
  const coffeeMats = collectMaterials(/coffee/i);
  const steamNodes = [];
  sceneRoot.traverse((o) => { if (/steam/i.test(o.name || '')) steamNodes.push(o); });
  let atmOn = true;
  let coffeeOn = true;
  let steamOn = true;
  function setEmissiveSet(list, on) {
    list.forEach((e) => {
      if (e.mat.emissiveIntensity !== undefined) e.mat.emissiveIntensity = on ? e.base * 1.15 : e.base * 0.05;
    });
  }
  function toggleSteam() {
    steamOn = !steamOn;
    steamNodes.forEach((n) => { n.visible = steamOn; });
    return steamOn;
  }

  // --------------------------------------------------------------- interactions
  const handlers = {
    light: (group) => {
      const g = LIGHT_GROUPS.find((x) => x.id === group);
      if (!g) return;
      const on = lighting.toggleGroup(group);
      uiState.patch({ lights: lighting.getState() });
      return on;
    },
    door: () => {
      door.toggle();
      uiState.patch({ doors: door.getState() });
    },
    toggle: (what) => {
      if (what === 'steam') toggleSteam();
      else if (what === 'atm') { atmOn = !atmOn; setEmissiveSet(atmMats, atmOn); }
      else if (what === 'coffee') { coffeeOn = !coffeeOn; setEmissiveSet(coffeeMats, coffeeOn); }
    },
    focus: (key) => {
      const p = FOCUS_POINTS[key];
      if (p) cameraSystem.focusOn(p.pos, p.dist);
    },
    car: (tag) => {
      traffic.demo(tag);
      ui.setCameraActive('vehicle');
      cameraSystem.setPreset('vehicle');
    },
  };

  const interaction = new InteractionSystem({
    camera: camera,
    dom: canvas,
    scene: sceneManager.scene,
    interactives: interactives,
    handlers: handlers,
  });

  // ------------------------------------------------------------------- wiring
  let targetTime = 18.5;
  let currentTime = 18.5;

  function requestTime(h, immediate) {
    targetTime = Math.max(0, Math.min(24, h));
    if (immediate) {
      currentTime = targetTime;
      dayNight.setTime(currentTime, true);
      uiState.patch({ timeOfDay: currentTime });
    }
  }

  function setPreset(name) {
    const map = { day: 9.0, dusk: 18.5, night: 22.0 };
    if (map[name] === undefined) return;
    requestTime(map[name], false);
    uiState.patch({ timeOfDay: map[name] });
  }

  function toggleRoof() {
    userRoofVisible = !userRoofVisible;
    autoCutaway = false;
    applyRoof();
    uiState.patch({ roofVisible: userRoofVisible });
  }

  let walkActive = false;
  function toggleWalk() {
    walkActive = !walkActive;
    if (walkActive) {
      cameraSystem.enterWalk();
      interaction.setEnabled(false);
      ui.setCameraActive('interior');
      autoCutaway = true;
      applyRoof();
    } else {
      cameraSystem.exitWalk();
      interaction.setEnabled(true);
      autoCutaway = false;
      applyRoof();
      ui.setCameraActive('hero');
    }
    uiState.patch({ walk: walkActive, cameraMode: walkActive ? 'walk' : 'orbit', roofVisible: !autoCutaway && userRoofVisible });
    ui.setWalk(walkActive);
  }

  function setCamera(name) {
    if (name === 'interior' || name === 'checkout') walkActive = false;
    cameraSystem.setPreset(name);
    uiState.patch({ cameraMode: name });
  }

  Object.assign(actions, {
    setPreset: setPreset,
    setTime: (h) => requestTime(h, false),
    toggleLight: (group, on) => {
      lighting.setGroupEnabled(group, on);
      uiState.patch({ lights: lighting.getState() });
    },
    setAllLights: (on) => {
      lighting.setAll(on);
      uiState.patch({ lights: lighting.getState() });
    },
    trafficToggle: (run) => {
      if (run) traffic.start(); else traffic.pause();
      uiState.patch({ traffic: traffic.getState() });
    },
    trafficReset: () => {
      traffic.reset();
      uiState.patch({ traffic: traffic.getState() });
    },
    trafficSpeed: (mult) => {
      traffic.setSpeed(mult);
      uiState.patch({ traffic: traffic.getState() });
    },
    demoCar: (tag) => handlers.car(tag),
    getVehicleState: (tag) => traffic.getVehicleState(tag),
    setVehicleDebug: (on) => traffic.setDebug(on),
    toggleVehicleDebug: () => traffic.setDebug(!traffic.debug),
    focusClerk: (tag) => {
      handlers.focus(tag === 'A' ? 'clerkA' : 'clerkB');
      clerk.trigger(tag);
    },
    setCamera: setCamera,
    toggleRoof: toggleRoof,
    toggleWalk: toggleWalk,
    resetCamera: () => {
      walkActive = false;
      cameraSystem.reset();
      uiState.patch({ cameraMode: 'hero', walk: false });
      ui.setWalk(false);
    },
    setQuality: (level) => {
      quality.set(level);
      uiState.patch({ quality: level });
    },
  });

  uiState.patch({ loaded: true, lights: lighting.getState(), traffic: traffic.getState(), doors: door.getState() });
  uiState.subscribe((state) => ui.syncState(state));
  ui.syncState(uiState.state);

  // --------------------------------------------------------------- frame loop
  const animation = new AnimationController();
  animation.register({
    update: (dt, elapsed) => {
      if (dt > 0) {
        traffic.update(dt);
        clerk.update(dt, elapsed);
        door.update(dt);
      } else {
        // paused: still evaluate door/clerks visually without advancing
        clerk.update(0, elapsed);
      }
    },
  });

  let uiTimer = 0;
  let qualityTimer = 0;
  let firstFrame = true;
  let freeCam = null;
  let freeCamFollow = null;
  const loop = new UpdateLoop((dt, rawDt, elapsed) => {
    if (Math.abs(targetTime - currentTime) > 0.01) {
      const step = 30 * rawDt;
      const diff = targetTime - currentTime;
      currentTime += Math.sign(diff) * Math.min(Math.abs(diff), step);
      dayNight.setTime(currentTime, true);
      uiState.patch({ timeOfDay: currentTime });
    }
    animation.update(dt, elapsed);
    cameraSystem.update(rawDt, elapsed);
    if (freeCamFollow) {
      const st = clerk.getDebugState();
      const c = st.clerks[freeCamFollow.tag];
      if (c) {
        const fx = Math.sin(c.yaw); const fz = Math.cos(c.yaw);
        const rx = Math.cos(c.yaw); const rz = -Math.sin(c.yaw);
        const px = c.position[0]; const pz = c.position[2];
        let cx; let cz; let cy;
        if (freeCamFollow.mode === 'front') {
          cx = px + fx * 3.2 + rx * 0.6; cz = pz + fz * 3.2 + rz * 0.6; cy = 2.05;
        } else if (freeCamFollow.mode === 'side') {
          cx = px + rx * 3.1 + fx * 0.4; cz = pz + rz * 3.1 + fz * 0.4; cy = 2.0;
        } else {
          cx = px - fx * 3.3 + rx * 1.0; cz = pz - fz * 3.3 + rz * 1.0; cy = 2.35;
        }
        cx = Math.max(-11.9, Math.min(11.9, cx));
        cz = Math.max(-6.95, Math.min(6.8, cz));
        camera.position.set(cx, cy, cz);
        camera.lookAt(px, 0.85, pz);
      }
    } else if (freeCam) {
      camera.position.set(freeCam.pos[0], freeCam.pos[1], freeCam.pos[2]);
      camera.lookAt(freeCam.target[0], freeCam.target[1], freeCam.target[2]);
    }
    rendererSystem.render(rawDt);

    uiTimer += rawDt;
    if (uiTimer > 0.4) {
      uiTimer = 0;
      const stats = rendererSystem.stats;
      uiState.state.fps = loop.fps;
      uiState.state.stats = stats;
      ui.setPerf(loop.fps, stats);
      // keep the live door / traffic readouts fresh for the UI + automation
      const ds = door.getState();
      if (ds.state !== uiState.state.doors.state || Math.abs((ds.progress || 0) - (uiState.state.doors.progress || 0)) > 0.05) {
        uiState.state.doors = ds;
      }
      const ts = traffic.getState();
      uiState.state.traffic.current = ts.current;
      uiState.state.traffic.phase = ts.phase;
      qualityTimer += 0.4;
      if (qualityTimer >= 1.0) {
        qualityTimer = 0;
        quality.tick(loop.fps);
        rendererSystem.tickPerformance(loop.fps);
      }
    }
    if (firstFrame) {
      firstFrame = false;
      ui.setLoading(1.0, '完成');
      setTimeout(() => ui.hideLoader(), 260);
      LAWSON.ready = true;
      document.body.dataset.ready = '1';
      traffic.setNight(currentTime < 7 || currentTime > 17.6);
    }
  });

  // keep the vehicle lights in sync with the clock
  const syncNight = (h) => traffic.setNight(h < 7 || h > 17.6);
  setInterval(() => { syncNight(currentTime); }, 2000);

  loop.start();

  // ------------------------------------------------------------------ public API
  const api = {
    setTimeOfDay: (h) => { requestTime(h, false); return targetTime; },
    setPreset: (name) => { setPreset(name); return targetTime; },
    setLight: (group, on) => { lighting.setGroupEnabled(group, on); uiState.patch({ lights: lighting.getState() }); return lighting.getState()[group]; },
    setAllLights: (on) => { lighting.setAll(on); uiState.patch({ lights: lighting.getState() }); },
    setCamera: (name) => { setCamera(name); return name; },
    toggleRoof: () => { toggleRoof(); return !autoCutaway && userRoofVisible; },
    setRoof: (v) => {
      userRoofVisible = !!v; autoCutaway = false; applyRoof();
      uiState.patch({ roofVisible: userRoofVisible });
      return userRoofVisible;
    },
    trafficStart: () => { traffic.start(); uiState.patch({ traffic: traffic.getState() }); },
    getClerkStates: () => clerk.getDebugState(),
    setClerkDebug: (on) => clerk.setDebug(on),
    notifyCustomer: (type, spot) => clerk.notifyCustomer(type, spot),
    clerkTrigger: (tag) => clerk.trigger(tag),
    clerkNav: (x, z, tx, tz) => clerk.debugNav(x, z, tx, tz),
    clerkForceTask: (tag, id) => clerk.forceTask(tag, id),
    clerkCamera: (tag, dist, height) => clerk.cameraFor(tag, dist, height),
    getVehicleState: (tag) => traffic.getVehicleState(tag),
    setVehicleDebug: (on) => traffic.setDebug(on),
    toggleVehicleDebug: () => traffic.setDebug(!traffic.debug),
    trafficPause: () => { traffic.pause(); uiState.patch({ traffic: traffic.getState() }); },
    trafficReset: () => { traffic.reset(); uiState.patch({ traffic: traffic.getState() }); },
    trafficSpeed: (mult) => { traffic.setSpeed(mult); uiState.patch({ traffic: traffic.getState() }); },
    demoCar: (tag) => handlers.car(tag),
    pauseAll: (v) => { animation.setPaused(v); loop.paused = v; uiState.patch({ paused: !!v }); },
    setQuality: (level) => { quality.set(level); uiState.patch({ quality: level }); return level; },
    hideUI: (v) => ui.hideUI(v),
    getStats: () => {
      const s = rendererSystem.stats;
      return {
        fps: loop.fps,
        drawCalls: s.drawCalls,
        triangles: s.triangles,
        programs: s.programs,
        lights: lighting.lights.length,
        quality: quality.level,
        timeOfDay: currentTime,
        pixelRatio: s.pixelRatio,
        renderSize: [s.width, s.height],
        batch: assetManager.batchReport || null,
      };
    },
    getState: () => uiState.state,
    toggleDoor: () => { door.toggle(); uiState.patch({ doors: door.getState() }); },
    setDoorsAutomatic: (v) => { door.setAutomatic(v); uiState.patch({ doors: door.getState() }); },
    toggleWalk: () => { toggleWalk(); return walkActive; },
    triggerClerk: (tag) => clerk.trigger(tag),
    focusOn: (key) => handlers.focus(key),
    focusPoint: (x, y, z, dist) => { cameraSystem.focusOn([x, y, z], dist || 4.0); },
    setFreeCamera: (pos, target) => { freeCam = { pos, target }; freeCamFollow = null; },
    clearFreeCamera: () => { freeCam = null; freeCamFollow = null; },
    followClerk: (tag, mode) => { freeCamFollow = { tag: tag || 'A', mode: mode || 'behind' }; freeCam = null; },
    // --- test / automation helpers (also handy for debugging) ---------------
    project: (worldPos) => {
      const v = new THREE.Vector3().fromArray(worldPos).project(camera);
      return [Math.round((v.x * 0.5 + 0.5) * window.innerWidth),
              Math.round((-v.y * 0.5 + 0.5) * window.innerHeight)];
    },
    pickAt: (x, y) => {
      const rect = canvas.getBoundingClientRect();
      const ndc = new THREE.Vector2(((x - rect.left) / rect.width) * 2 - 1,
                                   -((y - rect.top) / rect.height) * 2 + 1);
      const ray = new THREE.Raycaster();
      ray.setFromCamera(ndc, camera);
      const hits = ray.intersectObjects(interaction.meshes, false);
      for (const h of hits) {
        const e = h.object.userData.interaction;
        if (e) return { label: e.label, action: e.action, point: h.point.toArray() };
      }
      return null;
    },
    pickAll: (x, y) => {
      const rect = canvas.getBoundingClientRect();
      const ndc = new THREE.Vector2(((x - rect.left) / rect.width) * 2 - 1,
                                   -((y - rect.top) / rect.height) * 2 + 1);
      const ray = new THREE.Raycaster();
      ray.setFromCamera(ndc, camera);
      return ray.intersectObjects(interaction.meshes, false).slice(0, 8).map((h) => ({
        name: h.object.name,
        label: h.object.userData.interaction ? h.object.userData.interaction.label : null,
        dist: Math.round(h.distance * 10) / 10,
        point: h.point.toArray().map((v) => Math.round(v * 10) / 10),
      }));
    },
    entryInfo: (id) => {
      const e = interactives.find((x) => x.id === id);
      if (!e) return null;
      return {
        id: e.id, label: e.label, meshes: e.meshes.length,
        names: e.meshes.slice(0, 6).map((m) => m.name),
        box: { min: e.box.min.toArray(), max: e.box.max.toArray() },
      };
    },
    clickAt: (x, y) => {
      const rect = canvas.getBoundingClientRect();
      const ev = { clientX: x + rect.left, clientY: y + rect.top };
      interaction._updatePointer(ev);
      const hit = interaction._pick();
      if (!hit) return null;
      const e = hit.object.userData.interaction;
      if (!e) return null;
      interaction.activate(e.action);
      return { label: e.label, action: e.action };
    },
  };
  LAWSON.api = api;
  LAWSON.debugDoor = () => ({
    cam: camera.position.toArray().map((v) => Math.round(v * 100) / 100),
    sensor: door._sensorTriggered ? door._sensorTriggered() : null,
    progress: door.progress,
    target: door.target,
    state: door.state,
    automatic: door.automatic,
    leftPos: doorLeft ? doorLeft.position.toArray().map((v) => Math.round(v * 100) / 100) : null,
    leftBase: door.baseLeft ? door.baseLeft.toArray().map((v) => Math.round(v * 100) / 100) : null,
  });
  LAWSON.debug = {
    doorLeft: !!doorLeft,
    doorRight: !!doorRight,
    doorAvailable: door.available,
    roofTargets: roofTargets.length,
    interactives: interactives.map((e) => e.id),
    blockers: blockers.length,
    steamNodes: steamNodes.length,
    atmMaterials: atmMats.length,
    coffeeMaterials: coffeeMats.length,
    clerks: Object.keys(clerk.clerks || {}),
    cars: Object.keys(traffic.cars || {}),
    batch: assetManager.batchReport || null,
  };
  Object.defineProperty(LAWSON, 'state', {
    get: () => uiState.state,
    configurable: true,
  });

  // keyboard shortcuts
  window.addEventListener('keydown', (e) => {
    if (e.target && /input|textarea/i.test(e.target.tagName)) return;
    if (e.code === 'KeyR') { walkActive = false; cameraSystem.reset(); ui.setWalk(false); }
    else if (e.code === 'Digit1') setPreset('day');
    else if (e.code === 'Digit2') setPreset('dusk');
    else if (e.code === 'Digit3') setPreset('night');
    else if (e.code === 'Space') {
      e.preventDefault();
      traffic.running ? traffic.pause() : traffic.start();
      uiState.patch({ traffic: traffic.getState() });
    } else if (e.code === 'Escape' && walkActive) {
      toggleWalk();
    }
  });

  // start the traffic cycle a moment after load
  setTimeout(() => { traffic.start(); uiState.patch({ traffic: traffic.getState() }); }, 500);

  console.info('[Lawson] ready:', {
    interactives: interactives.length,
    blockers: blockers.length,
    emissives: prep.emissive.length,
    roofTargets: roofTargets.length,
    lights: lighting.lights.length,
  });
}

boot().catch((err) => {
  fatal(err && err.message ? err.message : String(err), null);
});
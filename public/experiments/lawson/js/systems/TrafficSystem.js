import * as THREE from 'three';
import {
  ROUTES, reverseRoute, exitRoute, SPEEDS, PHASES, IN_SPLIT, HOLD,
} from '../config/vehiclePaths.js';
import { VEHICLE_SPEC, SITE } from '../config/sceneConfig.js';

const UP = new THREE.Vector3(0, 1, 0);
const LOCAL_FWD = new THREE.Vector3(0, 0, -1);
const _q = new THREE.Quaternion();
const _v1 = new THREE.Vector3();
const _v2 = new THREE.Vector3();
const _v3 = new THREE.Vector3();
const _v4 = new THREE.Vector3();

function groundY(z) {
  if (z <= SITE.parkingZ[1]) return SITE.parkY;
  if (z <= SITE.aisleZ[1]) return SITE.aisleY;
  return SITE.roadY;
}

function yawFromForward(fx, fz) {
  return Math.atan2(-fx, -fz);
}

function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3); }
function easeInOutCubic(t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
function moveToward(cur, target, maxDelta) {
  if (Math.abs(target - cur) <= maxDelta) return target;
  return cur + Math.sign(target - cur) * maxDelta;
}

/**
 * Three-car traffic with three fully independent systems:
 *   1. BODY   : position / yaw along the route (holder)
 *   2. WHEELS : rolling angle integrated from the real travelled distance
 *               delta_theta = -delta_s / wheelRadius (forward), reversed when backing up
 *   3. STEER  : front wheel steering solved from the yaw rate (kinematic bicycle)
 *
 * State machine (one car on stage at a time):
 *   OFFSCREEN_WAIT -> APPROACHING -> TURNING_IN -> PARKING -> PARKED
 *   -> REVERSE_PREPARE -> REVERSING_OUT -> REVERSE_STOP -> SHIFT_TO_DRIVE
 *   -> ALIGNING_TO_EXIT -> DRIVING_OUT -> OFFSCREEN_RESET -> (next car)
 */
export class TrafficSystem {
  constructor(opts) {
    this.scene = opts.scene;
    this.assetManager = opts.assetManager;
    this.lighting = opts.lighting;
    this.cameraSystem = opts.cameraSystem || null;
    this.onStateChange = opts.onStateChange || null;
    this.speed = 1;
    this.running = false;
    this.night = false;
    this.cars = {};
    this.order = ['A', 'B', 'C'];
    this.currentIdx = 0;
    this.activeTag = null;
    this.idleTimer = 1.0;
    this.elapsed = 0;
    this.debug = false;
    this._hud = null;
    this._debugPaths = [];
    this._buildAll();
    this._buildDebug();
  }

  // --------------------------------------------------------------- building
  _buildAll() {
    this.order.forEach((tag) => { this.cars[tag] = this._buildCar(tag); });
  }

  _curve(points) {
    const pts = points.map((p) => new THREE.Vector3(p[0], groundY(p[1]), p[1]));
    const c = new THREE.CatmullRomCurve3(pts, false, 'centripetal', 0.35);
    c.arcLengthDivisions = 600;
    return c;
  }

  _buildCar(tag) {
    const spec = VEHICLE_SPEC[tag];
    const model = this.assetManager.cars[tag];
    const prepared = this.assetManager.prepareCar(tag);

    const holder = new THREE.Group();
    holder.name = 'CarHolder_' + tag;
    holder.visible = false;
    holder.rotation.order = 'YXZ';
    this.scene.add(holder);

    const inner = new THREE.Group();
    inner.name = 'CarBody_' + tag;
    inner.add(model);
    holder.add(inner);
    model.position.set(0, 0, 0);
    model.rotation.set(0, 0, 0);

    const inCurve = this._curve(ROUTES[tag].in);
    const inLen = inCurve.getLength();
    // audited slot x from the model root extras (fallback to the in-curve end)
    const slotX = (model.userData && typeof model.userData.slot_x === 'number')
      ? model.userData.slot_x
      : inCurve.getPointAt(1).x;
    const revCurve = this._curve(reverseRoute(slotX));
    const exitCurve = this._curve(exitRoute(slotX));
    const revLen = revCurve.getLength();
    const exitLen = exitCurve.getLength();

    const entrySegments = [
      { phase: PHASES.APPROACHING, from: IN_SPLIT[0], to: IN_SPLIT[1], speed: SPEEDS.approach },
      { phase: PHASES.TURNING_IN, from: IN_SPLIT[1], to: IN_SPLIT[2], speed: SPEEDS.turning },
      { phase: PHASES.PARKING, from: IN_SPLIT[2], to: IN_SPLIT[3], speed: SPEEDS.parking, ease: 'out' },
    ];
    entrySegments.forEach((s) => {
      s.duration = Math.max(0.3, (inLen * (s.to - s.from)) / s.speed);
    });

    const halfW = tag === 'B' ? 0.72 : 0.62;
    const frontZ = tag === 'A' ? -1.85 : (tag === 'B' ? -2.45 : -2.3);
    const rearZ = tag === 'A' ? 1.8 : (tag === 'B' ? 2.45 : 2.3);
    const lights = [];
    [-halfW, halfW].forEach((x) => {
      const spot = new THREE.SpotLight(new THREE.Color('#fff2dc'), 62, 30, 0.42, 0.72, 1.3);
      spot.position.set(x, 0.72, frontZ);
      spot.target.position.set(x * 1.2, 0.1, frontZ - 10);
      holder.add(spot);
      holder.add(spot.target);
      this.lighting.attachDynamicLight(spot, 'VehicleLights', 62);
      lights.push({ light: spot, kind: 'head' });
      const tail = new THREE.PointLight(new THREE.Color('#ff2a18'), 3.2, 6, 1.8);
      tail.position.set(x, 0.8, rearZ);
      holder.add(tail);
      this.lighting.attachDynamicLight(tail, 'VehicleLights', 3.2);
      lights.push({ light: tail, kind: 'tail' });
    });
    lights.forEach((l) => { l.light.userData.active = false; });

    const collectMats = (arr) => {
      const out = [];
      arr.forEach((item) => {
        item.obj.traverse((o) => {
          if (!o.isMesh) return;
          const mats = Array.isArray(o.material) ? o.material : [o.material];
          mats.forEach((m) => {
            if (!m) return;
            if (m.emissive && m.emissiveIntensity !== undefined) {
              out.push({ material: m, base: Math.max(0.6, m.emissiveIntensity) });
            }
          });
        });
      });
      return out;
    };

    const car = {
      tag: tag,
      spec: spec,
      rig: prepared,
      holder: holder,
      inner: inner,
      model: model,
      inCurve: inCurve,
      inLen: inLen,
      revCurve: revCurve,
      revLen: revLen,
      exitCurve: exitCurve,
      exitLen: exitLen,
      slotX: slotX,
      entrySegments: entrySegments,
      phase: PHASES.OFFSCREEN_WAIT,
      phaseTime: 0,
      entryIndex: 0,
      visible: false,
      v: 0,
      vPrev: 0,
      s: 0,
      yaw: 0,
      steer: 0,
      wheelSpin: 0,
      signedDist: 0,
      brake: false,
      reverseLamp: false,
      turn: 'none',
      blink: 0,
      prevPos: new THREE.Vector3(),
      hasPrev: false,
      wheelAngles: prepared.wheels.map(() => 0),
      headMats: collectMats(prepared.head),
      tailMats: collectMats(prepared.tail),
      turnLMats: collectMats(prepared.turnL),
      turnRMats: collectMats(prepared.turnR),
      reverseMats: collectMats(prepared.reverse),
      lights: lights,
    };
    this._resetWheelPose(car);
    return car;
  }

  _resetWheelPose(car) {
    car.rig.wheels.forEach((w, i) => {
      car.wheelAngles[i] = 0;
      w.obj.quaternion.copy(w.baseQuat);
    });
    car.rig.steers.forEach((s) => { s.obj.quaternion.copy(s.baseQuat); });
    car.steer = 0;
  }

  // ------------------------------------------------------------------ control
  start() {
    if (this.running) return;
    this.running = true;
    if (!this.activeTag) this._spawn(this.order[this.currentIdx]);
    this._emit();
  }

  pause() {
    this.running = false;
    this._emit();
  }

  setRunning(v) { v ? this.start() : this.pause(); }

  setSpeed(mult) {
    this.speed = clamp(mult, 0.15, 3);
    this._emit();
  }

  reset() {
    this.order.forEach((tag) => {
      const car = this.cars[tag];
      car.holder.visible = false;
      car.visible = false;
      car.phase = PHASES.OFFSCREEN_WAIT;
      car.phaseTime = 0;
      car.entryIndex = 0;
      car.v = 0;
      car.vPrev = 0;
      car.signedDist = 0;
      car.brake = false;
      car.reverseLamp = false;
      car.turn = 'none';
      this._resetWheelPose(car);
      this._setCarLightsActive(car, false);
      this._setEmissive(car.headMats, 0);
      this._setEmissive(car.tailMats, 0);
      this._setEmissive(car.turnLMats, 0);
      this._setEmissive(car.turnRMats, 0);
      this._setEmissive(car.reverseMats, 0);
    });
    this.activeTag = null;
    this.currentIdx = 0;
    this.idleTimer = 0.6;
    this._emit();
  }

  demo(tag) {
    if (!this.cars[tag]) return;
    this.reset();
    this.currentIdx = this.order.indexOf(tag);
    this.running = true;
    this.idleTimer = 0;
    this._spawn(tag);
    this._emit();
  }

  setNight(isNight) {
    this.night = !!isNight;
    this.order.forEach((tag) => {
      const car = this.cars[tag];
      const headOn = isNight ? 1.0 : 0.12;
      this._setEmissive(car.headMats, headOn);
      this._setEmissive(car.tailMats, isNight ? 0.9 : 0.1);
    });
  }

  _setCarLightsActive(car, active) {
    car.lights.forEach((entry) => { entry.light.userData.active = !!active; });
    this.lighting.refresh();
  }

  _setEmissive(list, factor) {
    list.forEach((entry) => {
      if (entry.material && entry.material.emissiveIntensity !== undefined) {
        entry.material.emissiveIntensity = entry.base * factor;
      }
    });
  }

  _emit() {
    if (!this.onStateChange) return;
    this.onStateChange(this.getState());
  }

  // ------------------------------------------------------------------ spawning
  _spawn(tag) {
    const car = this.cars[tag];
    this.activeTag = tag;
    car.phase = PHASES.APPROACHING;
    car.phaseTime = 0;
    car.entryIndex = 0;
    car.visible = true;
    car.hasPrev = false;
    car.v = SPEEDS.approach;
    car.vPrev = car.v;
    car.moveV = 0;
    car.signedDist = 0;
    car.holder.visible = true;
    car.holder.position.copy(car.inCurve.getPointAt(0));
    const tan = car.inCurve.getTangentAt(0);
    car.yaw = yawFromForward(tan.x, tan.z);
    car.holder.rotation.set(0, car.yaw, 0);
    this._resetWheelPose(car);
    this._setCarLightsActive(car, true);
    this._emit();
  }

  // ------------------------------------------------------------------- update
  update(dt) {
    this.elapsed += dt;
    if (!this.running) return;
    const scaled = dt * this.speed;
    const tag = this.activeTag;
    if (!tag) {
      this.idleTimer -= scaled;
      if (this.idleTimer <= 0) this._spawn(this.order[this.currentIdx]);
      return;
    }
    const car = this.cars[tag];
    this._updateCar(car, scaled);
    this._updateDebug(car);
  }

  _updateCar(car, dt) {
    const phase = car.phase;
    let moving = false;

    if (phase === PHASES.APPROACHING || phase === PHASES.TURNING_IN || phase === PHASES.PARKING) {
      moving = this._updateEntry(car, dt);
    } else if (phase === PHASES.PARKED) {
      car.phaseTime += dt;
      car.v = 0;
      car.brake = car.phaseTime < HOLD.parkBrakeOff;
      if (car.phaseTime >= car.spec.dwell) this._enter(car, PHASES.REVERSE_PREPARE);
    } else if (phase === PHASES.REVERSE_PREPARE) {
      car.phaseTime += dt;
      car.v = 0;
      car.brake = car.phaseTime < 0.35;
      car.reverseLamp = true;
      this._steerToZero(car, dt);
      if (car.phaseTime >= HOLD.reversePrepare) {
        car.s = 0;
        car.v = 0;
        this._enter(car, PHASES.REVERSING_OUT);
      }
    } else if (phase === PHASES.REVERSING_OUT) {
      moving = true;
      this._updateReverse(car, dt);
    } else if (phase === PHASES.REVERSE_STOP) {
      car.phaseTime += dt;
      car.v = 0;
      car.brake = true;
      car.reverseLamp = false;
      this._steerToZero(car, dt);
      if (car.phaseTime >= HOLD.reverseStop) this._enter(car, PHASES.SHIFT_TO_DRIVE);
    } else if (phase === PHASES.SHIFT_TO_DRIVE) {
      car.phaseTime += dt;
      car.v = 0;
      car.brake = car.phaseTime > HOLD.shiftToDrive - 0.2;
      car.reverseLamp = false;
      this._steerToZero(car, dt);
      if (car.phaseTime >= HOLD.shiftToDrive) {
        car.s = 0;
        car.v = 0;
        this._enter(car, PHASES.ALIGNING_TO_EXIT);
      }
    } else if (phase === PHASES.ALIGNING_TO_EXIT || phase === PHASES.DRIVING_OUT) {
      moving = true;
      this._updateExit(car, dt);
    } else if (phase === PHASES.OFFSCREEN_RESET) {
      car.phaseTime += dt;
      car.v = 0;
      if (car.phaseTime >= HOLD.offscreenReset) {
        car.holder.visible = false;
        car.visible = false;
        this._setCarLightsActive(car, false);
        this.activeTag = null;
        this.currentIdx = (this.currentIdx + 1) % this.order.length;
        this.idleTimer = HOLD.betweenCars;
        car.phase = PHASES.OFFSCREEN_WAIT;
        this._emit();
      }
    }

    if (moving) this._integrateWheelsAndSteer(car, dt);
    this._applyLights(car, dt);
  }

  _enter(car, phase) {
    car.phase = phase;
    car.phaseTime = 0;
    if (phase === PHASES.REVERSING_OUT || phase === PHASES.ALIGNING_TO_EXIT) car.moveV = 0;
    if (phase === PHASES.REVERSE_PREPARE) car.reverseLamp = true;
    if (phase === PHASES.PARKED || phase === PHASES.REVERSE_STOP || phase === PHASES.SHIFT_TO_DRIVE || phase === PHASES.DRIVING_OUT) car.reverseLamp = false;
    this._emit();
  }

  _updateEntry(car, dt) {
    const seg = car.entrySegments[car.entryIndex];
    car.phase = seg.phase;
    car.phaseTime += dt;
    const t = clamp(car.phaseTime / seg.duration, 0, 1);
    const tEased = seg.ease === 'out' ? easeOutCubic(t) : t;
    const u = seg.from + (seg.to - seg.from) * tEased;
    const pos = car.inCurve.getPointAt(u);
    const tan = car.inCurve.getTangentAt(u);
    car.v = t >= 1 ? 0 : seg.speed * (seg.ease === 'out' ? (1 - t) * 2 : 1);
    car.vPrev = car.v;
    this._placeCar(car, pos, yawFromForward(tan.x, tan.z));
    car.brake = seg.phase === PHASES.PARKING && t > 0.4;
    if (car.renderIndex !== undefined) car.renderIndex = car.entryIndex;
    if (t >= 1) {
      if (car.entryIndex < car.entrySegments.length - 1) {
        car.entryIndex += 1;
        car.phaseTime = 0;
        car.phase = car.entrySegments[car.entryIndex].phase;
      } else {
        // parked: snap to the exact slot end and settle
        car.holder.position.copy(car.inCurve.getPointAt(1));
        const endTan = car.inCurve.getTangentAt(1);
        car.yaw = yawFromForward(endTan.x, endTan.z);
        car.holder.rotation.set(0, car.yaw, 0);
        car.v = 0;
        car.vPrev = 0;
        car.brake = true;
        this._enter(car, PHASES.PARKED);
        return false;
      }
    }
    return true;
  }

  _updateReverse(car, dt) {
    const remaining = Math.max(0, car.revLen - car.s);
    const maxReverse = -SPEEDS.reverse;
    let v = car.moveV || 0;
    let target = maxReverse;
    if (remaining < 1.2) target = Math.max(maxReverse, -Math.sqrt(2 * SPEEDS.reverseBrake * remaining));
    if (v > target) v = moveToward(v, target, SPEEDS.reverseBrake * dt);
    else v = moveToward(v, target, SPEEDS.reverseAccel * dt);
    v = Math.min(0, v);
    car.moveV = v;
    car.s += -v * dt;
    if (car.s >= car.revLen - 1e-4) {
      car.s = car.revLen;
      car.holder.position.copy(car.revCurve.getPointAt(1));
      car.yaw = yawFromForward(...(() => {
        const t = car.revCurve.getTangentAt(1);
        return [-t.x, -t.z];
      })());
      car.holder.rotation.set(0, car.yaw, 0);
      car.brake = true;
      car.moveV = 0;
      this._enter(car, PHASES.REVERSE_STOP);
    } else {
      const u = clamp(car.s / car.revLen, 0, 1);
      car.holder.position.copy(car.revCurve.getPointAt(u));
      // car keeps facing -Z while backing up
      car.holder.rotation.set(0, car.yaw, 0);
      car.brake = v > -0.15;
    }
    car.reverseLamp = car.phase === PHASES.REVERSING_OUT;
    car.turn = 'none';
  }

  _updateExit(car, dt) {
    const remaining = Math.max(0, car.exitLen - car.s);
    let v = car.moveV || 0;
    // slow down through the bends (keeps the path physically believable)
    const steerLimit = clamp(1 - 1.9 * Math.abs(car.steer), 0.45, 1);
    let target = SPEEDS.exitCruise * steerLimit;
    if (remaining < 3.0) target = Math.min(target, Math.sqrt(2 * 1.6 * remaining) + 0.4);
    if (v < target) v = moveToward(v, target, SPEEDS.exitAccel * dt);
    else v = moveToward(v, target, 2.0 * dt);
    car.moveV = v;
    car.s += v * dt;
    const u = clamp(car.s / car.exitLen, 0, 1);
    const pos = car.exitCurve.getPointAt(u);
    const tan = car.exitCurve.getTangentAt(u);
    this._placeCar(car, pos, yawFromForward(tan.x, tan.z));
    car.phase = car.s < car.exitLen * 0.22 ? PHASES.ALIGNING_TO_EXIT : PHASES.DRIVING_OUT;
    car.brake = false;
    car.reverseLamp = false;
    car.turn = car.s > car.exitLen * 0.9 || Math.abs(car.steer) < 0.035 ? 'none' : 'right';
    if (car.s >= car.exitLen) {
      car.holder.position.copy(car.exitCurve.getPointAt(1));
      car.moveV = 0;
      this._enter(car, PHASES.OFFSCREEN_RESET);
    }
  }

  _placeCar(car, pos, yaw) {
    car.prevPos.copy(car.holder.position);
    car.holder.position.copy(pos);
    car.yaw = yaw;
    car.holder.rotation.set(0, yaw, 0);
    car.hasPrev = true;
  }

  _steerToZero(car, dt) {
    car.steer += (0 - car.steer) * Math.min(1, dt * 7);
    this._applySteer(car);
  }

  _applySteer(car) {
    car.rig.steers.forEach((s) => {
      s.obj.quaternion.copy(s.baseQuat).multiply(_q.setFromAxisAngle(s.steerAxisLocal, car.steer));
    });
  }

  /**
   * Wheel rolling + steering, both derived from the ACTUAL movement.
   * delta_theta = -delta_s / radius (forward), + when backing up -> automatic.
   */
  _integrateWheelsAndSteer(car, dt) {
    if (!car.hasPrev) { car.hasPrev = true; return; }
    _v1.copy(car.holder.position).sub(car.prevPos);
    const dist = _v1.length();
    _v2.copy(LOCAL_FWD).applyQuaternion(car.holder.quaternion).normalize();
    const dsForward = _v1.dot(_v2);
    car.signedDist += dsForward;

    const prevYaw = car._prevYaw !== undefined ? car._prevYaw : car.yaw;
    let dyaw = car.yaw - prevYaw;
    while (dyaw > Math.PI) dyaw -= Math.PI * 2;
    while (dyaw < -Math.PI) dyaw += Math.PI * 2;
    car._prevYaw = car.yaw;
    const yawRate = dyaw / Math.max(1e-4, dt);
    const vF = dsForward / Math.max(1e-4, dt);
    car.vF = vF;
    car.v = Math.abs(vF);

    car.rig.wheels.forEach((w, i) => {
      car.wheelAngles[i] -= dsForward / Math.max(0.05, w.radius);
      w.obj.quaternion.copy(w.baseQuat).multiply(_q.setFromAxisAngle(w.spinAxisLocal, car.wheelAngles[i]));
    });

    // kinematic bicycle: yawRate = v / L * tan(delta)  ->  delta = atan(L * yawRate / v)
    let target = 0;
    if (Math.abs(vF) > 0.12 && Math.abs(dist) > 1e-6) {
      target = Math.atan2(car.spec.wheelbase * yawRate, vF);
      target = clamp(target, -0.55, 0.55);
    }
    car.steer += (target - car.steer) * Math.min(1, dt * 9);
    this._applySteer(car);

    // entry turning indicator (right turn into the slot)
    if (car.phase === PHASES.TURNING_IN) car.turn = 'left';
    else if (car.phase === PHASES.APPROACHING) car.turn = 'none';
    car.prevPos.copy(car.holder.position);
  }

  _applyLights(car, dt) {
    const night = this.night;
    this._setEmissive(car.headMats, night ? 1.0 : 0.12);
    this._setEmissive(car.tailMats, car.brake ? 2.0 : (night ? 1.0 : 0.1));
    this._setEmissive(car.reverseMats, car.reverseLamp ? 2.4 : 0.0);
    if (car.turn === 'none') {
      car.blink = 0;
      this._setEmissive(car.turnLMats, 0);
      this._setEmissive(car.turnRMats, 0);
    } else {
      car.blink += dt;
      const on = Math.floor(car.blink / 0.34) % 2 === 0;
      this._setEmissive(car.turnRMats, car.turn === 'right' && on ? 1.25 : 0);
      this._setEmissive(car.turnLMats, car.turn === 'left' && on ? 1.25 : 0);
    }
  }

  // ---------------------------------------------------------------- telemetry
  getState() {
    const tag = this.activeTag;
    const car = tag ? this.cars[tag] : null;
    return {
      enabled: this.running,
      running: this.running,
      current: tag || this.order[this.currentIdx],
      phase: car ? car.phase : PHASES.OFFSCREEN_WAIT,
      speed: this.speed,
      activePosition: car ? car.holder.position.toArray() : null,
      reverseLamp: car ? car.reverseLamp : false,
      brake: car ? car.brake : false,
    };
  }

  getVehicleState(tag) {
    const car = this.cars[tag];
    if (!car) return null;
    const wheels = car.rig.wheels.map((w, i) => ({
      name: w.name,
      radius: Number(w.radius.toFixed(4)),
      angle: Number(car.wheelAngles[i].toFixed(4)),
      deg: Number((car.wheelAngles[i] * 180 / Math.PI).toFixed(2)),
    }));
    return {
      tag,
      phase: car.phase,
      visible: car.holder.visible,
      position: car.holder.position.toArray().map((v) => Number(v.toFixed(3))),
      yaw: Number(car.yaw.toFixed(4)),
      v: car.vF !== undefined ? Math.abs(Number(car.vF.toFixed(3))) : 0,
      vForward: car.vF !== undefined ? Number(car.vF.toFixed(3)) : 0,
      signedDist: Number(car.signedDist.toFixed(3)),
      steer: Number(car.steer.toFixed(4)),
      wheelSpinTotal: Number(car.wheelAngles.reduce((a, b) => a + b, 0).toFixed(4)),
      wheels,
      wheelbase: car.spec.wheelbase,
      track: car.spec.track,
      reverseLamp: !!car.reverseLamp,
      reverseMaterials: car.reverseMats.length,
      reverseEmissive: car.reverseMats.length ? Number(car.reverseMats[0].material.emissiveIntensity.toFixed(2)) : 0,
      brake: !!car.brake,
      turn: car.turn,
      active: this.activeTag === tag,
    };
  }

  // ------------------------------------------------------------------- debug
  _buildDebug() {
    this.order.forEach((tag) => {
      const car = this.cars[tag];
      const group = new THREE.Group();
      group.name = 'VehicleDebug_' + tag;
      group.visible = false;
      car.holder.add(group);

      const fwdArrow = new THREE.ArrowHelper(new THREE.Vector3(0, 0, -1), new THREE.Vector3(0, 2.1, 0), 2.2, 0x35ff7a, 0.45, 0.25);
      const velArrow = new THREE.ArrowHelper(new THREE.Vector3(0, 0, -1), new THREE.Vector3(0, 1.75, 0), 1.8, 0x35c8ff, 0.4, 0.22);
      group.add(fwdArrow);
      group.add(velArrow);

      const axleGeom = new THREE.BufferGeometry();
      axleGeom.setAttribute('position', new THREE.BufferAttribute(new Float32Array(4 * 2 * 3), 3));
      const axleLines = new THREE.LineSegments(axleGeom, new THREE.LineBasicMaterial({ color: 0xff49e0 }));
      group.add(axleLines);

      car.debug = { group, fwdArrow, velArrow, axleLines };

      const pathGroup = new THREE.Group();
      pathGroup.name = 'VehiclePaths_' + tag;
      pathGroup.visible = false;
      this.scene.add(pathGroup);
      const mkLine = (curve, color) => {
        const pts = curve.getPoints(140);
        const geo = new THREE.BufferGeometry().setFromPoints(pts);
        return new THREE.Line(geo, new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.85 }));
      };
      const inLine = mkLine(car.inCurve, 0x4aa8ff);
      const revLine = mkLine(car.revCurve, 0xffb140);
      const outLine = mkLine(car.exitCurve, 0x54e07a);
      pathGroup.add(inLine, revLine, outLine);
      this._debugPaths.push(pathGroup);
      car.debug.paths = pathGroup;
    });

    const hud = document.createElement('div');
    hud.id = 'vehicle-debug-hud';
    hud.style.cssText = 'position:fixed;left:12px;bottom:44px;z-index:60;display:none;' +
      'padding:8px 10px;border-radius:8px;background:rgba(8,12,24,.78);color:#cfe3ff;' +
      'font:11px/1.5 ui-monospace,Consolas,monospace;white-space:pre;pointer-events:none;' +
      'border:1px solid rgba(90,140,220,.45)';
    document.body.appendChild(hud);
    this._hud = hud;
  }

  setDebug(on) {
    this.debug = !!on;
    this.order.forEach((tag) => {
      const car = this.cars[tag];
      car.debug.group.visible = this.debug;
      car.debug.paths.visible = this.debug && this.activeTag === tag;
    });
    if (this._hud) this._hud.style.display = this.debug ? 'block' : 'none';
    return this.debug;
  }

  _updateDebug(activeCar) {
    if (!this.debug) return;
    this.order.forEach((tag) => {
      const car = this.cars[tag];
      car.debug.paths.visible = this.activeTag === tag;
    });
    const car = activeCar || (this.activeTag ? this.cars[this.activeTag] : null);
    if (!car) { if (this._hud) this._hud.textContent = 'vehicle debug: idle'; return; }
    const dbg = car.debug;
    const fwd = _v1.copy(LOCAL_FWD).applyQuaternion(car.holder.quaternion).normalize();
    dbg.fwdArrow.position.set(0, 2.1, 0);
    dbg.fwdArrow.setDirection(fwd);
    dbg.velArrow.position.set(0, 1.75, 0);
    if (car.hasPrev) {
      _v2.copy(car.holder.position).sub(car.prevPos);
      if (_v2.lengthSq() > 1e-8) dbg.velArrow.setDirection(_v2.normalize());
    }
    // wheel axle markers
    const pos = dbg.axleLines.geometry.attributes.position;
    const right = _v3.set(1, 0, 0).applyQuaternion(car.holder.quaternion).normalize();
    let k = 0;
    car.rig.wheels.forEach((w) => {
      w.obj.getWorldPosition(_v1);
      car.holder.worldToLocal(_v1);
      const half = _v4.copy(right).multiplyScalar(0.42);
      pos.setXYZ(k++, _v1.x - half.x, _v1.y - half.y, _v1.z - half.z);
      pos.setXYZ(k++, _v1.x + half.x, _v1.y + half.y, _v1.z + half.z);
    });
    pos.needsUpdate = true;
    if (this._hud) {
      const wheels = car.rig.wheels.map((w, i) => car.wheelAngles[i].toFixed(2)).join(' ');
      this._hud.textContent =
        'VEHICLE DEBUG  [V] toggle\n' +
        'car   : ' + car.tag + '  (' + car.spec.name + ')\n' +
        'state : ' + car.phase + '\n' +
        'speed : ' + car.v.toFixed(2) + ' m/s   steer ' + (car.steer * 180 / Math.PI).toFixed(1) + '°\n' +
        'lights: reverse=' + (car.reverseLamp ? 'ON' : 'off') + '  brake=' + (car.brake ? 'ON' : 'off') + '  turn=' + car.turn + '\n' +
        'wheels: ' + car.rig.wheels.map((w) => w.name.replace('car' + car.tag + '_', '')).join(' ') + '\n' +
        'angles: ' + wheels + ' rad';
    }
  }
}
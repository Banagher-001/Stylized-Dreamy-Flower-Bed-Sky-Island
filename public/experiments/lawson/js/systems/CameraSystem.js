import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CAMERA_PRESETS, CAMERA_LIMITS, INTERIOR } from '../config/sceneConfig.js';

const _v = new THREE.Vector3();

/** Orbit camera with smooth preset flights, interior walk mode and vehicle follow cam. */
export class CameraSystem {
  constructor(camera, domElement, opts) {
    this.camera = camera;
    this.dom = domElement;
    this.controls = new OrbitControls(camera, domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = CAMERA_LIMITS.dampingFactor;
    this.controls.minDistance = CAMERA_LIMITS.minDistance;
    this.controls.maxDistance = CAMERA_LIMITS.maxDistance;
    this.controls.maxPolarAngle = CAMERA_LIMITS.maxPolarAngle;
    this.controls.minPolarAngle = CAMERA_LIMITS.minPolarAngle;
    this.controls.target.set(0, 2.2, 5);
    this.controls.enabled = true;

    this.blockers = opts.blockers || [];
    this.onCutawayNeeded = opts.onCutawayNeeded || null;
    this.getActiveCar = opts.getActiveCar || null;

    this.mode = 'orbit';                 // orbit | walk | follow
    this.tween = null;
    this.keys = {};
    this.walk = { yaw: Math.PI, pitch: 0, speed: 2.4, pos: new THREE.Vector3() };
    this.vehicleFollow = true;

    camera.position.fromArray(CAMERA_PRESETS.hero.pos);
    this.controls.target.fromArray(CAMERA_PRESETS.hero.target);
    this.controls.update();
    this.currentPreset = 'hero';

    this._bindKeys();
    this._bindPointerLock();
  }

  _bindKeys() {
    window.addEventListener('keydown', (e) => {
      this.keys[e.code] = true;
      if (e.code === 'Escape' && this.mode === 'walk') this.exitWalk();
    });
    window.addEventListener('keyup', (e) => { this.keys[e.code] = false; });
  }

  _bindPointerLock() {
    document.addEventListener('pointerlockchange', () => {
      if (document.pointerLockElement !== this.dom && this.mode === 'walk') {
        // pointer lock lost -> stay in walk mode but without mouse look
      }
    });
    document.addEventListener('mousemove', (e) => {
      if (this.mode !== 'walk' || document.pointerLockElement !== this.dom) return;
      this.walk.yaw -= e.movementX * 0.0026;
      this.walk.pitch -= e.movementY * 0.0022;
      this.walk.pitch = Math.max(-1.25, Math.min(1.25, this.walk.pitch));
    });
  }

  setPreset(name) {
    const preset = CAMERA_PRESETS[name];
    if (!preset) return;
    this.currentPreset = name;
    if (this.mode === 'walk') this.exitWalk(true);
    if (name === 'vehicle') {
      this.mode = 'follow';
      this.controls.enabled = false;
      if (this.onCutawayNeeded) this.onCutawayNeeded(false);
      return;
    }
    this.mode = 'orbit';
    this.controls.enabled = true;
    this.startTween(preset.pos, preset.target);
    if (name === 'interior' || name === 'checkout') {
      if (this.onCutawayNeeded) this.onCutawayNeeded(true);
    } else if (this.onCutawayNeeded) {
      this.onCutawayNeeded(false);
    }
  }

  startTween(pos, target, duration) {
    this.tween = {
      fromPos: this.camera.position.clone(),
      toPos: new THREE.Vector3().fromArray(pos),
      fromTarget: this.controls.target.clone(),
      toTarget: new THREE.Vector3().fromArray(target),
      t: 0,
      duration: duration || 1.15,
    };
  }

  reset() {
    this.setPreset('hero');
  }

  focusOn(point, distance) {
    const target = new THREE.Vector3().fromArray(point);
    const dir = new THREE.Vector3(0, 0.45, 1).normalize();
    const pos = target.clone().add(dir.multiplyScalar(distance || 5.2));
    this.mode = 'orbit';
    this.controls.enabled = true;
    this.startTween(pos.toArray(), target.toArray(), 1.0);
    this.currentPreset = 'focus';
  }

  enterWalk() {
    this.mode = 'walk';
    this.controls.enabled = false;
    const p = new THREE.Vector3(0.4, INTERIOR.eyeHeight, 5.6);
    this.camera.position.copy(p);
    this.walk.pos.copy(p);
    this.walk.yaw = Math.PI;
    this.walk.pitch = -0.05;
    if (this.onCutawayNeeded) this.onCutawayNeeded(true);
    if (this.dom.requestPointerLock) this.dom.requestPointerLock();
    return true;
  }

  exitWalk(silent) {
    if (this.mode !== 'walk') return false;
    this.mode = 'orbit';
    this.controls.enabled = true;
    if (document.pointerLockElement === this.dom) document.exitPointerLock();
    this.controls.target.set(0, 2.2, 5);
    this.camera.position.fromArray(CAMERA_PRESETS.hero.pos);
    this.controls.update();
    if (!silent && this.onCutawayNeeded) this.onCutawayNeeded(false);
    return true;
  }

  _walkUpdate(dt) {
    const k = this.keys;
    const forward = (k['KeyW'] ? 1 : 0) - (k['KeyS'] ? 1 : 0);
    const strafe = (k['KeyD'] ? 1 : 0) - (k['KeyA'] ? 1 : 0);
    const boost = k['ShiftLeft'] || k['ShiftRight'] ? 1.9 : 1;
    if (forward || strafe) {
      const speed = this.walk.speed * boost * dt;
      const sin = Math.sin(this.walk.yaw);
      const cos = Math.cos(this.walk.yaw);
      const dx = (-sin * forward + cos * strafe) * speed;
      const dz = (-cos * forward - sin * strafe) * speed;
      const next = this.walk.pos.clone();
      next.x += dx;
      next.z += dz;
      // interior bounds
      next.x = Math.max(INTERIOR.walkBoundsX[0], Math.min(INTERIOR.walkBoundsX[1], next.x));
      next.z = Math.max(INTERIOR.walkBoundsZ[0], Math.min(INTERIOR.walkBoundsZ[1], next.z));
      // blockers (AABB) with a small radius
      const r = 0.32;
      for (const box of this.blockers) {
        const inside = next.x > box.min.x - r && next.x < box.max.x + r && next.z > box.min.z - r && next.z < box.max.z + r;
        if (!inside) continue;
        const dxIn = Math.min(Math.abs(next.x - (box.min.x - r)), Math.abs(next.x - (box.max.x + r)));
        const dzIn = Math.min(Math.abs(next.z - (box.min.z - r)), Math.abs(next.z - (box.max.z + r)));
        if (dxIn < dzIn) next.x = this.walk.pos.x;
        else next.z = this.walk.pos.z;
      }
      this.walk.pos.copy(next);
    }
    this.walk.pos.y = INTERIOR.eyeHeight + Math.sin(this.time * 6.0) * (forward || strafe ? 0.012 : 0);
    this.camera.position.copy(this.walk.pos);
    const dir = new THREE.Vector3(
      -Math.sin(this.walk.yaw) * Math.cos(this.walk.pitch),
      Math.sin(this.walk.pitch),
      -Math.cos(this.walk.yaw) * Math.cos(this.walk.pitch),
    );
    this.camera.lookAt(_v.copy(this.walk.pos).add(dir));
  }

  _followUpdate() {
    const car = this.getActiveCar ? this.getActiveCar() : null;
    if (!car) return;
    const p = car.holder.position;
    const yaw = car.holder.rotation.y;
    const dist = 13.0;
    const height = 4.6;
    const side = 3.4;
    const behind = new THREE.Vector3(
      Math.sin(yaw) * dist + Math.cos(yaw) * side,
      height,
      Math.cos(yaw) * dist - Math.sin(yaw) * side,
    );
    const target = new THREE.Vector3(
      p.x - Math.sin(yaw) * 3.2,
      p.y + 1.1,
      p.z - Math.cos(yaw) * 3.2,
    );
    this.camera.position.lerp(_v.copy(p).add(behind), 0.05);
    this.controls.target.lerp(target, 0.07);
    this.camera.lookAt(this.controls.target);
  }

  update(dt, elapsed) {
    this.time = elapsed || 0;
    if (this.tween) {
      this.tween.t += dt;
      const raw = Math.min(1, this.tween.t / this.tween.duration);
      const e = raw < 0.5 ? 4 * raw * raw * raw : 1 - Math.pow(-2 * raw + 2, 3) / 2;
      this.camera.position.lerpVectors(this.tween.fromPos, this.tween.toPos, e);
      this.controls.target.lerpVectors(this.tween.fromTarget, this.tween.toTarget, e);
      this.camera.lookAt(this.controls.target);
      if (raw >= 1) this.tween = null;
      this.controls.update();
      return;
    }
    if (this.mode === 'walk') {
      this._walkUpdate(dt);
    } else if (this.mode === 'follow') {
      this._followUpdate();
    } else {
      this.controls.update();
    }
  }
}
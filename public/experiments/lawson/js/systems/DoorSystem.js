import * as THREE from 'three';
import { DOOR_ANCHOR } from '../config/sceneConfig.js';

const CLOSED = 'CLOSED';
const OPENING = 'OPENING';
const OPEN = 'OPEN';
const CLOSING = 'CLOSING';

/** Sliding entrance doors driven by the two door-leaf pivots found in the GLB. */
export class DoorSystem {
  constructor(model, camera) {
    this.left = model.doorLeft;
    this.right = model.doorRight;
    this.camera = camera;
    this.state = CLOSED;
    this.progress = 0;          // 0 closed, 1 open
    this.target = 0;
    this.holdTimer = 0;
    this.automatic = true;
    this.manualOpen = false;
    this.manualTimer = 0;
    this.onChange = null;
    this.sensor = DOOR_ANCHOR.sensor;
    if (this.left) this.baseLeft = this.left.position.clone();
    if (this.right) this.baseRight = this.right.position.clone();
    this.travel = DOOR_ANCHOR.slideTravel;
    this.speed = 1 / Math.max(0.3, DOOR_ANCHOR.openTime);
  }

  get available() { return !!(this.left || this.right); }

  setAutomatic(on) {
    this.automatic = !!on;
    if (!this.automatic) this.target = this.manualOpen ? 1 : 0;
    return this.automatic;
  }

  /** Click / button: toggles the manual override. */
  toggle() {
    this.manualOpen = !this.manualOpen;
    this.manualTimer = 10;          // manual override beats the proximity sensor
    this.target = this.manualOpen ? 1 : 0;
    return this.manualOpen;
  }

  open() { this.manualOpen = true; this.manualTimer = 10; this.target = 1; }
  close() { this.manualOpen = false; this.manualTimer = 0; this.target = 0; }

  /** proximity sensor for the automatic mode (camera based) */
  _sensorTriggered() {
    if (!this.camera) return false;
    const p = this.camera.position;
    const dz = p.z - DOOR_ANCHOR.z;
    const dx = p.x - DOOR_ANCHOR.x;
    const near = Math.sqrt(dx * dx + dz * dz) < this.sensor;
    const inside = p.z < DOOR_ANCHOR.z;
    // only react when walking near the entrance / orbiting into the store area
    return near && Math.abs(p.y - DOOR_ANCHOR.y) < 3.2 && (inside || p.z < DOOR_ANCHOR.z + 5.0);
  }

  update(dt) {
    if (!this.available) return;
    if (this.manualTimer > 0) {
      this.manualTimer = Math.max(0, this.manualTimer - dt);
      this.target = this.manualOpen ? 1 : 0;
    } else if (this.automatic) {
      if (this._sensorTriggered()) { this.target = 1; this.holdTimer = DOOR_ANCHOR.holdTime; }
      else if (this.target > 0) {
        this.holdTimer -= dt;
        if (this.holdTimer <= 0) this.target = 0;
      }
    }
    const dir = this.target > this.progress ? 1 : -1;
    if (Math.abs(this.target - this.progress) > 0.001) {
      this.progress = Math.max(0, Math.min(1, this.progress + dir * this.speed * dt));
      const next = dir > 0 ? OPENING : CLOSING;
      if (next !== this.state) this._setState(next);
    } else if (this.progress >= 0.999 && this.state !== OPEN) this._setState(OPEN);
    else if (this.progress <= 0.001 && this.state !== CLOSED) this._setState(CLOSED);

    const e = this.progress * this.progress * (3 - 2 * this.progress);
    if (this.left) this.left.position.x = this.baseLeft.x - this.travel * e;
    if (this.right) this.right.position.x = this.baseRight.x + this.travel * e;
  }

  _setState(s) {
    this.state = s;
    if (this.onChange) this.onChange({ state: s, progress: this.progress });
  }

  getState() {
    return { state: this.state, isOpen: this.progress > 0.5, progress: this.progress, automatic: this.automatic };
  }
}
/**
 * Procedural Minecraft-style animation library for the two blocky clerks.
 * Every pose is a set of DELTAS (radians) on top of each joint's rest rotation;
 * the controller blends them smoothly so motions never snap.
 *
 * Joints: head, shoulderL, shoulderR, elbowL, elbowR, hipL, hipR
 * Model forward is local +Z, so a negative shoulder X rotation swings the arm forward.
 */
const JOINTS = ['head', 'shoulderL', 'shoulderR', 'elbowL', 'elbowR', 'hipL', 'hipR'];

function zeroPose() {
  const p = { bob: 0, lean: 0 };
  JOINTS.forEach((j) => { p[j] = { x: 0, y: 0, z: 0 }; });
  return p;
}

function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }

export class AnimLibrary {
  constructor() {
    this.state = 'Idle_Stand';
    this.time = 0;
    this.phase = 0;
    this.speed = 0;
    this.cur = zeroPose();
    this.target = zeroPose();
    this.blend = 9.0;
    this.stateTime = 0;
    this.carry = false;
  }

  setState(name, opts = {}) {
    if (this.state !== name) {
      this.state = name;
      this.stateTime = 0;
    }
    if (opts.speed !== undefined) this.speed = opts.speed;
    if (opts.carry !== undefined) this.carry = !!opts.carry;
  }

  /** Pose targets for the current state (deltas in radians). */
  _poseFor(state, t, sp) {
    const p = zeroPose();
    const breathe = Math.sin(t * 1.7);
    const swing = Math.sin(this.phase);
    const swing2 = Math.sin(this.phase + Math.PI);
    switch (state) {
      case 'Walk_Normal':
        p.hipL.x = swing * 0.55;
        p.hipR.x = swing2 * 0.55;
        p.shoulderL.x = -swing * 0.34;
        p.shoulderR.x = -swing2 * 0.34;
        p.elbowL.x = -0.10 - Math.max(0, swing) * 0.12;
        p.elbowR.x = -0.10 - Math.max(0, swing2) * 0.12;
        p.head.y = Math.sin(this.phase * 0.5) * 0.06;
        p.bob = Math.abs(Math.sin(this.phase)) * 0.018;
        break;
      case 'Walk_Carry':
        p.hipL.x = swing * 0.34;
        p.hipR.x = swing2 * 0.34;
        p.shoulderL.x = -1.05;
        p.shoulderR.x = -1.05;
        p.elbowL.x = -0.20;
        p.elbowR.x = -0.20;
        p.bob = Math.abs(Math.sin(this.phase)) * 0.012;
        p.head.x = 0.04;
        break;
      case 'Idle_Stand':
        p.head.y = Math.sin(t * 0.42) * 0.10;
        p.shoulderL.z = 0.035 + breathe * 0.012;
        p.shoulderR.z = -0.035 - breathe * 0.012;
        p.bob = breathe * 0.005;
        break;
      case 'Idle_LookAround':
        p.head.y = Math.sin(t * 0.75) * 0.55;
        p.head.x = Math.sin(t * 0.33) * 0.08;
        p.shoulderL.z = 0.035; p.shoulderR.z = -0.035;
        p.bob = breathe * 0.005;
        break;
      case 'Idle_ShiftWeight':
        p.head.y = Math.sin(t * 0.35) * 0.22;
        p.hipL.z = 0.05 + Math.sin(t * 0.5) * 0.03;
        p.hipR.z = -0.05 - Math.sin(t * 0.5) * 0.03;
        p.bob = Math.sin(t * 1.15) * 0.008;
        break;
      case 'Wait':
        p.head.y = Math.sin(t * 0.3) * 0.18;
        p.bob = Math.sin(t * 1.1) * 0.006;
        break;
      case 'Greet':
        // right arm out to the side, small wave; left arm relaxed
        p.shoulderR.z = -1.85 + Math.sin(t * 9.0) * 0.16;
        p.shoulderR.x = -0.25;
        p.elbowR.x = -0.35;
        p.shoulderL.z = 0.05;
        p.head.y = -0.12;
        p.head.x = -0.04;
        p.bob = Math.sin(t * 1.6) * 0.004;
        break;
      case 'Talk':
        p.shoulderR.x = -0.55 + Math.sin(t * 2.2) * 0.12;
        p.shoulderR.z = -0.30;
        p.elbowR.x = -0.55 + Math.sin(t * 2.2 + 0.5) * 0.12;
        p.shoulderL.x = -0.22;
        p.head.y = Math.sin(t * 0.9) * 0.16;
        p.head.x = 0.03;
        break;
      case 'Cashier_Scan':
        p.shoulderL.x = -1.02 + Math.sin(t * 3.4) * 0.10;
        p.shoulderR.x = -0.98 + Math.sin(t * 3.4 + 1.6) * 0.16;
        p.elbowL.x = -0.38; p.elbowR.x = -0.36;
        p.head.x = 0.28;
        p.head.y = Math.sin(t * 1.1) * 0.10;
        p.bob = Math.sin(t * 3.4) * 0.003;
        break;
      case 'Cashier_Bag':
        p.shoulderL.x = -0.72; p.shoulderR.x = -0.72;
        p.elbowL.x = -0.62 + Math.sin(t * 2.6) * 0.10;
        p.elbowR.x = -0.62 + Math.sin(t * 2.6 + Math.PI) * 0.10;
        p.head.x = 0.22;
        break;
      case 'Shelf_Inspect':
        p.shoulderL.x = -0.80 + Math.sin(t * 1.2) * 0.08;
        p.shoulderR.x = -0.80 + Math.sin(t * 1.2 + 1.2) * 0.08;
        p.elbowL.x = -0.30; p.elbowR.x = -0.30;
        p.head.x = 0.12 + Math.sin(t * 0.5) * 0.05;
        p.head.y = Math.sin(t * 0.7) * 0.18;
        break;
      case 'Shelf_Reach_High':
        p.shoulderR.x = -2.15 + Math.sin(t * 1.6) * 0.08;
        p.shoulderR.z = -0.18;
        p.elbowR.x = -0.30;
        p.shoulderL.x = -0.35;
        p.head.x = -0.16;
        p.head.y = 0.10;
        p.bob = Math.sin(t * 1.6) * 0.004;
        break;
      case 'Shelf_Reach_Low':
        p.shoulderR.x = -0.62 + Math.sin(t * 2.0) * 0.10;
        p.shoulderL.x = -0.48;
        p.elbowR.x = -0.42; p.elbowL.x = -0.22;
        p.head.x = 0.34;
        p.head.y = Math.sin(t * 0.9) * 0.16;
        p.bob = -0.012 + Math.sin(t * 2.0) * 0.004;
        break;
      case 'Shelf_Restock':
        p.shoulderR.x = -0.95 + Math.sin(t * 2.6) * 0.18;
        p.shoulderL.x = -0.80 + Math.sin(t * 2.6 + 2.0) * 0.18;
        p.elbowR.x = -0.45; p.elbowL.x = -0.45;
        p.head.x = 0.22;
        p.head.y = Math.sin(t * 1.2) * 0.12;
        break;
      case 'Box_Pickup':
        p.shoulderL.x = -0.70; p.shoulderR.x = -0.70;
        p.elbowL.x = -0.50; p.elbowR.x = -0.50;
        p.head.x = 0.46 + Math.sin(t * 2.0) * 0.06;
        p.hipL.x = 0.16; p.hipR.x = 0.16;
        p.bob = -0.020;
        break;
      case 'Box_Putdown':
        p.shoulderL.x = -0.55; p.shoulderR.x = -0.55;
        p.elbowL.x = -0.42; p.elbowR.x = -0.42;
        p.head.x = 0.38;
        p.hipL.x = 0.10; p.hipR.x = 0.10;
        p.bob = -0.012;
        break;
      case 'Fridge_Inspect':
        p.shoulderL.x = -1.25 + Math.sin(t * 1.1) * 0.06;
        p.shoulderR.x = -1.05 + Math.sin(t * 1.1 + 1.4) * 0.08;
        p.elbowL.x = -0.28; p.elbowR.x = -0.30;
        p.head.x = 0.16;
        p.head.y = Math.sin(t * 0.8) * 0.14;
        p.bob = Math.sin(t * 1.3) * 0.004;
        break;
      case 'Counter_Clean':
        p.shoulderL.x = -0.88 + Math.sin(t * 3.0) * 0.08;
        p.shoulderR.x = -0.92 + Math.sin(t * 3.0 + 1.5) * 0.10;
        p.shoulderL.z = Math.sin(t * 3.0) * 0.18;
        p.shoulderR.z = Math.sin(t * 3.0 + 1.2) * 0.16;
        p.elbowL.x = -0.45; p.elbowR.x = -0.42;
        p.head.x = 0.26;
        break;
      case 'Floor_Clean':
        p.shoulderR.x = -0.72 + Math.sin(t * 2.4) * 0.10;
        p.shoulderR.z = -0.22 + Math.sin(t * 2.4) * 0.35;
        p.elbowR.x = -0.28;
        p.shoulderL.x = -0.15;
        p.head.x = 0.24;
        p.head.y = Math.sin(t * 1.1) * 0.12;
        p.bob = Math.sin(t * 2.4) * 0.004;
        break;
      case 'Table_Clean':
        p.shoulderL.x = -0.95 + Math.sin(t * 2.7) * 0.12;
        p.shoulderR.x = -0.90 + Math.sin(t * 2.7 + 1.8) * 0.12;
        p.elbowL.x = -0.55; p.elbowR.x = -0.52;
        p.head.x = 0.30;
        p.head.y = Math.sin(t * 0.8) * 0.14;
        break;
      default:
        p.bob = breathe * 0.005;
        break;
    }
    return p;
  }

  update(dt, opts = {}) {
    this.time += dt;
    this.stateTime += dt;
    if (opts.speed !== undefined) this.speed = opts.speed;
    if (opts.carry !== undefined) this.carry = !!opts.carry;
    const stride = 1.30;
    this.phase += (this.speed / stride) * Math.PI * 2 * dt * (opts.speed > 0.02 ? 1 : 0);
    if (opts.speed > 0.02) this.target = this._poseFor(this.state, this.time, opts.speed);
    else this.target = this._poseFor(this.state, this.time, 0);

    const k = Math.min(1, dt * this.blend);
    this.cur.bob += (this.target.bob - this.cur.bob) * k;
    JOINTS.forEach((j) => {
      const c = this.cur[j]; const t = this.target[j];
      c.x += (t.x - c.x) * k;
      c.y += (t.y - c.y) * k;
      c.z += (t.z - c.z) * k;
    });
    return this.cur;
  }
}
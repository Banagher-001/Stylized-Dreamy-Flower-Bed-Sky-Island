import * as THREE from 'three';
import { NavGrid } from './clerk/NavGrid.js';
import { AnimLibrary } from './clerk/AnimLibrary.js';
import { TaskManager } from './clerk/TaskManager.js';
import {
  CLERK_PROFILES, CUSTOMER_SPOTS, CUSTOMER_EVENT, STORE, TASKS,
} from './clerk/clerkConfig.js';

const JOINTS = ['head', 'shoulderL', 'shoulderR', 'elbowL', 'elbowR', 'hipL', 'hipR'];

const STATE = {
  IDLE: 'IDLE',
  SELECT_TASK: 'SELECT_TASK',
  WALK_TO_TARGET: 'WALK_TO_TARGET',
  TURN_TO_TARGET: 'TURN_TO_TARGET',
  PERFORM_TASK: 'PERFORM_TASK',
  TASK_COMPLETE: 'TASK_COMPLETE',
  SHORT_WAIT: 'SHORT_WAIT',
  RETURN_POST: 'RETURN_POST',
  PICKUP_ITEM: 'PICKUP_ITEM',
  CARRY_ITEM: 'CARRY_ITEM',
  RESTOCK_SHELF: 'RESTOCK_SHELF',
  INTERACT_WITH_CUSTOMER: 'INTERACT_WITH_CUSTOMER',
  ASSIST_CUSTOMER: 'ASSIST_CUSTOMER',
  CASHIER_SERVICE: 'CASHIER_SERVICE',
  INTERRUPTED: 'INTERRUPTED',
  RESUME_TASK: 'RESUME_TASK',
};

function wrapAngle(a) {
  while (a > Math.PI) a -= Math.PI * 2;
  while (a < -Math.PI) a += Math.PI * 2;
  return a;
}
function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
function rand(a, b) { return a + Math.random() * (b - a); }
function dist2(ax, az, bx, bz) { return Math.hypot(ax - bx, az - bz); }

/**
 * Two Minecraft-style clerk NPCs with an autonomous task scheduler,
 * grid path-finding, procedural animations and a customer-interaction interface.
 */
export class ClerkSystem {
  constructor(scene, opts = {}) {
    this.scene = scene;
    this.opts = opts;
    this.time = 0;
    this.debug = false;
    this.nav = new NavGrid();
    this.tm = new TaskManager();
    this.clerks = {};
    this.customerQueue = [];
    this.customerDemo = CUSTOMER_EVENT.autoDemo;
    this.demoTimer = rand(CUSTOMER_EVENT.minInterval, CUSTOMER_EVENT.maxInterval);
    this.eventLog = [];
    this.eventCounts = { enter: 0, checkout: 0, help: 0 };
    this.lastHudUpdate = 0;
    this._hud = null;
    this._buildClerks();
    this._buildProps();
    this._buildHud();
    Object.keys(this.clerks).forEach((tag) => {
      const c = this.clerks[tag];
      this._enterSelect(c);
    });
  }

  // ------------------------------------------------------------------ build
  _buildClerks() {
    ['A', 'B'].forEach((tag) => {
      const prof = CLERK_PROFILES[tag];
      const root = this.scene.getObjectByName('clerk' + tag + '_root');
      if (!root) { console.warn('[ClerkSystem] missing root for clerk ' + tag); return; }
      const joints = {};
      JOINTS.forEach((j) => {
        const node = this.scene.getObjectByName('clerk' + tag + '_' + j);
        if (node) {
          joints[j] = {
            node,
            base: { x: node.rotation.x, y: node.rotation.y, z: node.rotation.z },
          };
        }
      });
      // 旧版 GLB 里店员 B 的静态抱箱（clerkB_carryBox，挂在肘关节）会一直显示；
      // 新版模型已删除该道具，这里再做一次兼容隐藏，避免旧缓存页面出现常驻箱子。
      const legacyBox = this.scene.getObjectByName('clerk' + tag + '_carryBox');
      if (legacyBox) legacyBox.visible = false;
      const baseQuat = root.quaternion.clone();
      const fwd = new THREE.Vector3(0, 0, 1).applyQuaternion(baseQuat);
      const baseYaw = Math.atan2(fwd.x, fwd.z);
      const home = prof.home;
      const c = {
        tag,
        profile: prof,
        root,
        joints,
        baseYaw,
        baseRootRot: { x: root.rotation.x, y: root.rotation.y, z: root.rotation.z },
        pos: new THREE.Vector3(home.x, 0, home.z),
        yaw: Math.atan2(home.face[0], home.face[1]),
        home: { x: home.x, z: home.z, face: home.face },
        state: STATE.IDLE,
        stateTime: 0,
        anim: new AnimLibrary(),
        task: null,
        interrupted: null,
        path: null,
        pathIndex: 0,
        faceTarget: null,
        afterWalk: null,
        speed: 0,
        taskTimer: 0,
        taskDuration: 0,
        taskAnimIndex: -1,
        customer: null,
        serviceStep: 0,
        serviceTimer: 0,
        carry: false,
        tool: null,
        props: {},
        stats: { tasksDone: 0, distance: 0, interruptions: 0 },
      };
      root.position.set(home.x, 0, home.z);
      root.rotation.set(c.baseRootRot.x, this._yawToRotation(c, c.yaw), c.baseRootRot.z);
      this.clerks[tag] = c;
    });
  }

  _buildProps() {
    ['A', 'B'].forEach((tag) => {
      const c = this.clerks[tag];
      if (!c) return;
      // carried carton: low-poly cardboard box (centred geometry, follows the chest)
      {
        const holder = new THREE.Group();
        holder.name = 'clerk' + tag + '_carryBox';
        const cardboard = new THREE.MeshStandardMaterial({ color: '#b98a56', roughness: 0.88 });
        const tape = new THREE.MeshStandardMaterial({ color: '#e3d2a8', roughness: 0.7 });
        const body = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.22, 0.26), cardboard);
        body.castShadow = true;
        const strip = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.045, 0.055), tape);
        strip.position.set(0, 0.10, 0);
        body.add(strip);
        holder.add(body);
        holder.position.set(0, 0.72, 0.34);
        holder.visible = false;
        c.root.add(holder);
        c.props.box = holder;
      }
      // simple low-poly broom for cleaning tasks
      const broom = new THREE.Group();
      const handle = new THREE.Mesh(
        new THREE.CylinderGeometry(0.012, 0.012, 0.74, 6),
        new THREE.MeshStandardMaterial({ color: '#8a5a33', roughness: 0.8 }),
      );
      handle.position.set(0, -0.37, 0);
      const head = new THREE.Mesh(
        new THREE.BoxGeometry(0.22, 0.035, 0.09),
        new THREE.MeshStandardMaterial({ color: '#d8c38a', roughness: 0.9 }),
      );
      head.position.set(0, -0.74, 0.035);
      broom.add(handle, head);
      broom.visible = false;
      const handAnchor = new THREE.Group();
      handAnchor.position.set(0, -0.20, 0.02);
      const elbow = c.joints.elbowR ? c.joints.elbowR.node : c.root;
      elbow.add(handAnchor);
      handAnchor.add(broom);
      c.props.broom = broom;
      c.props.broomAnchor = handAnchor;
    });
  }

  _buildHud() {
    const hud = document.createElement('div');
    hud.id = 'clerk-debug-hud';
    hud.style.cssText = 'position:fixed;right:12px;bottom:44px;z-index:60;display:none;' +
      'padding:8px 10px;border-radius:8px;background:rgba(8,12,24,.80);color:#d7e5ff;' +
      'font:11px/1.45 ui-monospace,Consolas,monospace;white-space:pre;pointer-events:none;' +
      'border:1px solid rgba(90,140,220,.45)';
    document.body.appendChild(hud);
    this._hud = hud;
  }

  // --------------------------------------------------------------- utilities
  _yawToRotation(c, yaw) {
    // model forward is local +Z; convert a world heading into the root's Y rotation
    return c.baseRootRot.y + wrapAngle(yaw - c.baseYaw);
  }

  _applyPose(c, pose) {
    JOINTS.forEach((j) => {
      const joint = c.joints[j];
      if (!joint) return;
      const p = pose[j];
      joint.node.rotation.set(
        joint.base.x + p.x,
        joint.base.y + p.y,
        joint.base.z + p.z,
      );
    });
    c.root.position.y = pose.bob;
    c.root.rotation.y = this._yawToRotation(c, c.yaw);
  }

  _showBox(c, on) {
    if (c.props.box) c.props.box.visible = !!on;
    c.carry = !!on;
  }

  _showBroom(c, on) {
    if (c.props.broom) c.props.broom.visible = !!on;
    c.tool = on ? 'broom' : null;
  }

  _walkAnim(c, speed) {
    const state = c.carry ? 'Walk_Carry' : 'Walk_Normal';
    c.anim.setState(state, { speed, carry: c.carry });
  }

  _faceTo(c, x, z) {
    c.faceTarget = Math.atan2(x - c.pos.x, z - c.pos.z);
  }

  _beginWalk(c, targetX, targetZ, afterWalk, faceAfter = null) {
    const path = this.nav.findPath(c.pos.x, c.pos.z, targetX, targetZ);
    if (!path || !path.length) {
      // no path: cancel gracefully (pick next task)
      c.afterWalk = null;
      c.state = STATE.TASK_COMPLETE;
      c.stateTime = 0;
      c.path = null;
      return false;
    }
    c.path = path;
    c.pathIndex = 0;
    c.afterWalk = afterWalk || null;
    c.faceAfterWalk = faceAfter;
    c.state = STATE.WALK_TO_TARGET;
    c.stateTime = 0;
    c.speed = 0;
    this._walkAnim(c, 0);
    return true;
  }

  // ------------------------------------------------------------ state machine
  _enterSelect(c) {
    c.state = STATE.SELECT_TASK;
    c.stateTime = 0;
  }

  _chooseTask(c) {
    const other = this._otherClerk(c.tag);
    const otherInfo = other ? {
      tag: other.tag,
      taskId: other.task ? other.task.id : null,
      area: other.task ? other.task.area : null,
      target: other.task ? other.task.target : null,
    } : null;
    const task = this.tm.choose(c.tag, {
      position: { x: c.pos.x, z: c.pos.z },
      other: otherInfo,
      forceTaskId: c.forceTaskId,
    });
    c.forceTaskId = null;
    c.task = task;
    c.taskDuration = task.duration;
    this._log(c.tag, 'task:start', task.id + ' @' + task.area);
    this._startTask(c);
  }

  _startTask(c) {
    const t = c.task;
    if (!t) { this._enterSelect(c); return; }
    if (t.carry && t.pickup) {
      // restock: walk to the stock-room pickup first
      c.afterWalk = () => {
        c.state = STATE.PICKUP_ITEM;
        c.stateTime = 0;
        c.anim.setState('Box_Pickup');
      };
      if (!this._beginWalk(c, t.pickup.x, t.pickup.z, c.afterWalk)) return;
      c.pendingWalk = { x: t.target.x, z: t.target.z, phase: 'carry' };
      return;
    }
    if (t.tool === 'broom') this._showBroom(c, true);
    const face = t.target.face;
    c.afterWalk = () => {
      c.state = STATE.TURN_TO_TARGET;
      c.stateTime = 0;
      c.faceTarget = Math.atan2(face[0], face[1]);
      c.afterTurn = () => {
        c.state = STATE.PERFORM_TASK;
        c.stateTime = 0;
        c.taskTimer = 0;
        c.taskAnimIndex = -1;
      };
    };
    this._beginWalk(c, t.target.x, t.target.z, c.afterWalk);
  }

  _completeTask(c) {
    if (!c.task) { this._enterSelect(c); return; }
    this.tm.complete(c.tag, c.task);
    this._log(c.tag, 'task:done', c.task.id);
    c.task = null;
    c.state = STATE.TASK_COMPLETE;
    c.stateTime = 0;
    if (c.tag === 'A') this._returnPostChance = 0.45;
  }

  _finishPerform(c) {
    const t = c.task;
    if (!t) { this._enterSelect(c); return; }
    if (t.tool === 'broom') this._showBroom(c, false);
    if (t.carry) this._showBox(c, false);
    // task is finished here (record history/cooldown immediately, so a return walk
    // or an interruption can never re-run the same task)
    this.tm.complete(c.tag, t);
    c.stats.tasksDone += 1;
    this._log(c.tag, 'task:done', t.id);
    c.task = null;
    c.speed = 0;
    // occasionally return to the post before choosing the next task
    if (c.tag === 'A' && Math.random() < 0.45 && dist2(c.pos.x, c.pos.z, c.home.x, c.home.z) > 2.0) {
      c.afterWalk = () => { c.state = STATE.SHORT_WAIT; c.stateTime = 0; c.waitDuration = rand(1.4, 3.2); c.anim.setState('Idle_ShiftWeight'); };
      if (this._beginWalk(c, c.home.x, c.home.z, c.afterWalk, c.home.face)) {
        this._log(c.tag, 'return-post', t.id);
        return;
      }
    }
    c.state = STATE.TASK_COMPLETE;
    c.stateTime = 0;
  }

  _otherClerk(tag) {
    return this.clerks[tag === 'A' ? 'B' : 'A'] || null;
  }

  _log(tag, evt, detail) {
    this.eventLog.push({ t: this.time, tag, evt, detail });
    if (this.eventLog.length > 400) this.eventLog.shift();
  }

  // ---------------------------------------------------------- customer events
  notifyCustomer(type, spotName) {
    const spot = CUSTOMER_SPOTS[spotName] || CUSTOMER_SPOTS.checkout;
    const evt = { type, spotName: spotName || 'checkout', spot, at: this.time, handled: false };
    this.customerQueue.push(evt);
    if (this.eventCounts[type] !== undefined) this.eventCounts[type] += 1;
    this._log('sys', 'customer:' + type, evt.spotName);
    return evt;
  }

  _hasPendingCheckout() {
    return this.customerQueue.some((e) => !e.handled && (e.type === 'checkout' || e.type === 'enter'));
  }

  _checkCustomerPriorities() {
    const a = this.clerks.A;
    if (!a) return;
    const pending = this.customerQueue.find((e) => !e.handled && e.type === 'checkout');
    const enter = this.customerQueue.find((e) => !e.handled && e.type === 'enter');
    if (pending && a.state !== STATE.CASHIER_SERVICE && !a.customer) {
      // clerk A drops non-cashier work and returns to the register
      this._interrupt(a, 'checkout', pending);
    } else if (enter && !pending && a.state !== STATE.CASHIER_SERVICE && !a.customer &&
      a.state !== STATE.WALK_TO_TARGET) {
      this._interrupt(a, 'enter', enter);
    }
    // clerk B only offers extra support when the queue is long and A is already serving
    const b = this.clerks.B;
    const queueLen = this.customerQueue.filter((e) => e.type === 'checkout' && !e.handled).length;
    if (b && pending && queueLen >= 2 && a.state === STATE.CASHIER_SERVICE &&
      !b.carry && b.state !== STATE.ASSIST_CUSTOMER && b.state !== STATE.CASHIER_SERVICE &&
      b.state !== STATE.PICKUP_ITEM && b.state !== STATE.RESTOCK_SHELF && Math.random() < 0.01) {
      b.interrupted = b.interrupted || (b.task ? { task: b.task, remaining: Math.max(0.5, b.taskDuration - b.taskTimer), phase: b.state } : null);
      this._sendToCustomer(b, pending, true);
    }
  }

  _interrupt(c, customerType, evt) {
    if (c.customer) return;
    if (c.task && (c.state === STATE.PERFORM_TASK || c.state === STATE.WALK_TO_TARGET)) {
      c.interrupted = {
        task: c.task,
        remaining: Math.max(0.5, c.taskDuration - c.taskTimer),
        phase: c.state,
      };
      c.stats.interruptions += 1;
      this._log(c.tag, 'task:interrupt', c.task.id + ' for ' + customerType);
      if (c.task.tool === 'broom') this._showBroom(c, false);
      if (c.task.carry) this._showBox(c, false);
    }
    c.task = null;
    this._sendToCustomer(c, evt, false);
  }

  _sendToCustomer(c, evt, assist) {
    const spot = c.tag === 'A'
      ? CUSTOMER_SPOTS.checkout
      : (assist || evt.type === 'checkout') ? CUSTOMER_SPOTS.checkoutSupport : evt.spot;
    c.customer = { evt, assist, type: evt.type };
    c.state = STATE.WALK_TO_TARGET;
    c.stateTime = 0;
    c.anim.setState('Walk_Normal', { speed: 0 });
    c.afterWalk = () => {
      c.state = STATE.TURN_TO_TARGET;
      c.stateTime = 0;
      c.faceTarget = Math.atan2(spot.face[0], spot.face[1]);
      c.afterTurn = () => {
        c.state = assist ? STATE.ASSIST_CUSTOMER : STATE.CASHIER_SERVICE;
        c.stateTime = 0;
        c.serviceStep = 0;
        c.serviceTimer = 0;
      };
    };
    const ok = this._beginWalk(c, spot.x, spot.z, c.afterWalk);
    if (!ok) {
      const near = this.nav.nearestWalkable(spot.x, spot.z, 2.5);
      if (near) { c.pos.x = near[0]; c.pos.z = near[1]; c.holderSafe = true; }
      c.state = c.assist ? STATE.ASSIST_CUSTOMER : STATE.CASHIER_SERVICE;
      c.serviceStep = 0; c.serviceTimer = 0; c.afterWalk = null;
    }
  }

  _finishCustomer(c) {
    const isCheckoutOwner = c.tag === 'A';
    const isAssist = c.customer && c.customer.assist;
    if (c.customer && c.customer.evt && isCheckoutOwner) c.customer.evt.handled = true;
    if (!isAssist) c.stats.customersServed = (c.stats.customersServed || 0) + 1;
    this._log(c.tag, 'customer:done', c.customer ? c.customer.type : '-');
    c.customer = null;
    if (c.interrupted) {
      const it = c.interrupted;
      c.interrupted = null;
      c.task = it.task;
      c.taskDuration = it.task.duration;
      c.taskTimer = Math.max(0.5, it.remaining);
      c.state = STATE.RESUME_TASK;
      c.stateTime = 0;
      // walk back to the interrupted task target
      c.afterWalk = () => {
        c.state = STATE.PERFORM_TASK;
        c.stateTime = 0;
        c.taskTimer = Math.max(0.5, it.remaining);
        c.taskAnimIndex = -1;
      };
      this._beginWalk(c, it.task.target.x, it.task.target.z, c.afterWalk);
    } else {
      this._enterSelect(c);
    }
  }

  // ------------------------------------------------------------------- update
  update(dt) {
    this.time += dt;
    this.tm.tick(dt);
    this._demoTick(dt);
    this._checkCustomerPriorities();
    Object.keys(this.clerks).forEach((tag) => this._updateClerk(this.clerks[tag], dt));
    this._separateClerks(dt);
    if (this.debug) this._updateHud(dt);
  }

  _demoTick(dt) {
    if (!this.customerDemo) return;
    this.demoTimer -= dt;
    if (this.demoTimer > 0) return;
    this.demoTimer = rand(CUSTOMER_EVENT.minInterval, CUSTOMER_EVENT.maxInterval);
    const r = Math.random();
    if (r < CUSTOMER_EVENT.checkoutChance) this.notifyCustomer('checkout', 'checkout');
    else if (r < CUSTOMER_EVENT.checkoutChance + CUSTOMER_EVENT.enterChance) this.notifyCustomer('enter', 'entrance');
    else this.notifyCustomer('help', Math.random() < 0.5 ? 'aisleHelp' : 'shelfHelp');
  }

  _updateClerk(c, dt) {
    c.stateTime += dt;
    if (c.props.box && c.props.box.visible && (!c.task || c.task.id !== 'restock')) this._showBox(c, false);
    // 箱子只在「取货 / 抱箱行走 / 上架」这三个状态可见；任何异常中断都立即收起，
    // 避免任务切换/卡死保护后箱子一直挂在店员胸前。
    if (c.props.box && c.props.box.visible) {
      const carrying = c.state === STATE.PICKUP_ITEM || c.state === STATE.CARRY_ITEM || c.state === STATE.RESTOCK_SHELF;
      if (!carrying) this._showBox(c, false);
    }
    if (c.customer) {
      this._updateCustomerState(c, dt);
      return;
    }
    switch (c.state) {
      case STATE.IDLE: this._enterSelect(c); break;
      case STATE.SELECT_TASK:
        if (c.stateTime > rand(0.1, 0.3)) this._chooseTask(c);
        break;
      case STATE.WALK_TO_TARGET: this._updateWalk(c, dt); break;
      case STATE.TURN_TO_TARGET: {
        const rate = STORE.turnSpeed * dt;
        const d = wrapAngle(c.faceTarget - c.yaw);
        c.yaw += clamp(d, -rate, rate);
        if (Math.abs(d) < 0.06) {
          c.yaw = c.faceTarget;
          const cb = c.afterTurn; c.afterTurn = null;
          if (cb) cb();
        }
        c.anim.setState('Idle_Stand', { speed: 0 });
        c.anim.update(dt, { speed: 0 });
        this._applyPose(c, c.anim.cur);
        break;
      }
      case STATE.PERFORM_TASK: c.speed = 0; this._updatePerform(c, dt); break;
      case STATE.PICKUP_ITEM: this._updatePickup(c, dt); break;
      case STATE.CARRY_ITEM: this._updateCarry(c, dt); break;
      case STATE.RESTOCK_SHELF: this._updateRestock(c, dt); break;
      case STATE.TASK_COMPLETE:
        if (c.stateTime > 0.25) this._enterSelect(c);
        break;
      case STATE.SHORT_WAIT:
        c.anim.setState('Idle_ShiftWeight', { speed: 0 });
        c.anim.update(dt, { speed: 0 });
        this._applyPose(c, c.anim.cur);
        if (c.stateTime > (c.waitDuration || 2)) this._enterSelect(c);
        break;
      case STATE.RETURN_POST: {
        this._updateWalk(c, dt);
        break;
      }
      case STATE.RESUME_TASK:
        // wait a beat and then continue the saved task
        if (c.stateTime > 0.3) {
          c.anim.setState('Walk_Normal', { speed: 0 });
          c.state = STATE.WALK_TO_TARGET;
        }
        break;
      default:
        this._enterSelect(c);
    }
  }

  _updateWalk(c, dt) {
    if (!c.path || c.pathIndex >= c.path.length) {
      c.state = STATE.TURN_TO_TARGET;
      c.stateTime = 0;
      const cb = c.afterWalk; c.afterWalk = null;
      if (cb) cb();
      return;
    }
    const wp = c.path[c.pathIndex];
    const dx = wp.x - c.pos.x;
    const dz = wp.z - c.pos.z;
    const d = Math.hypot(dx, dz);
    const remaining = d + (c.path.length - 1 - c.pathIndex) * 0.3;
    const targetSpeed = c.profile.speed * (remaining < 0.75 ? 0.45 : 1);
    const accel = 2.4;
    if (c.speed < targetSpeed) c.speed = Math.min(targetSpeed, c.speed + accel * dt);
    else c.speed = Math.max(targetSpeed, c.speed - accel * 1.6 * dt);

    if (d < 0.06) {
      c.pathIndex += 1;
      return;
    }
    const step = Math.min(d, c.speed * dt);
    let nx = c.pos.x + (dx / d) * step;
    let nz = c.pos.z + (dz / d) * step;
    let moved = false;
    if (this.nav.walkable(nx, nz)) moved = true;
    else if (this.nav.walkable(nx, c.pos.z)) { nz = c.pos.z; moved = true; }       // slide along X
    else if (this.nav.walkable(c.pos.x, nz)) { nx = c.pos.x; moved = true; }       // slide along Z
    if (!moved) {
      // try a few short probing steps in alternate directions (corner sliding)
      const probe = Math.max(0.12, step);
      for (let a = 1; a <= 8; a++) {
        const ang = Math.atan2(dx, dz) + (a % 2 ? 1 : -1) * Math.ceil(a / 2) * (Math.PI / 4);
        const px = c.pos.x + Math.sin(ang) * probe;
        const pz = c.pos.z + Math.cos(ang) * probe;
        if (this.nav.walkable(px, pz)) { nx = px; nz = pz; moved = true; break; }
      }
    }
    if (moved) {
      c.stats.distance += Math.hypot(nx - c.pos.x, nz - c.pos.z);
      c.pos.x = nx; c.pos.z = nz;
      c.stuckTimer = 0;
    } else {
      c.stuckTimer = (c.stuckTimer || 0) + dt;
      const t = c.path[c.path.length - 1];
      if ((c.stuckTimer > 1.2) && (c._lastRepath || 0) < this.time - 1.0) {
        c._lastRepath = this.time;
        const path = this.nav.findPath(c.pos.x, c.pos.z, t.x, t.z);
        if (path) { c.path = path; c.pathIndex = 0; }
      }
      if (c.stuckTimer > 3.2) {
        // truly stuck: snap to the nearest walkable cell and continue
        const near = this.nav.nearestWalkable(c.pos.x, c.pos.z, 2.0);
        if (near) {
          const path = this.nav.findPath(near[0], near[1], t.x, t.z);
          if (path) { c.pos.x = near[0]; c.pos.z = near[1]; c.path = path; c.pathIndex = 0; c.stuckTimer = 0; c._lastRepath = this.time; }
        }
        if (c.stuckTimer > 4.5) {
        c.stuckTimer = 0;
        this._showBox(c, false);
        this._showBroom(c, false);
        c.state = STATE.TASK_COMPLETE;
        c.stateTime = 0;
        c.task = null;
      }
      }
    }
    const dirYaw = Math.atan2(dx, dz);
    const dy = wrapAngle(dirYaw - c.yaw);
    c.yaw += clamp(dy, -STORE.turnSpeed * dt * 0.9, STORE.turnSpeed * dt * 0.9);
    this._walkAnim(c, c.speed);
    c.anim.update(dt, { speed: c.speed, carry: c.carry });
    this._applyPose(c, c.anim.cur);
    c.root.position.x = c.pos.x;
    c.root.position.z = c.pos.z;
  }

  _taskAnim(c, dt) {
    const t = c.task;
    if (!t) return;
    c.taskTimer += dt;
    const progress = clamp(c.taskTimer / Math.max(0.2, c.taskDuration), 0, 1);
    const idx = Math.min(t.anims.length - 1, Math.floor(progress * t.anims.length));
    if (idx !== c.taskAnimIndex) { c.taskAnimIndex = idx; c.anim.setState(t.anims[idx]); }
    c.anim.update(dt, { speed: 0, carry: c.carry });
    this._applyPose(c, c.anim.cur);
    if (c.taskTimer >= c.taskDuration) this._finishPerform(c);
  }

  _updatePerform(c, dt) {
    this._taskAnim(c, dt);
  }

  _updatePickup(c, dt) {
    c.anim.setState('Box_Pickup');
    c.anim.update(dt, { speed: 0 });
    this._applyPose(c, c.anim.cur);
    if (c.stateTime > 1.5) {
      this._showBox(c, true);
      this._log(c.tag, 'box:pickup', c.task ? c.task.id : '-');
      c.state = STATE.CARRY_ITEM;
      c.stateTime = 0;
      const t = c.task;
      c.afterWalk = () => {
        c.state = STATE.TURN_TO_TARGET;
        c.stateTime = 0;
        c.faceTarget = Math.atan2(t.target.face[0], t.target.face[1]);
        c.afterTurn = () => {
          c.state = STATE.RESTOCK_SHELF;
          c.stateTime = 0;
          c.taskTimer = 0;
          c.taskAnimIndex = -1;
        };
      };
      this._beginWalk(c, t.target.x, t.target.z, c.afterWalk);
      c.state = STATE.CARRY_ITEM;
    }
  }

  _updateCarry(c, dt) {
    this._updateWalk(c, dt);
  }

  _updateRestock(c, dt) {
    const t = c.task;
    if (!t) { this._enterSelect(c); return; }
    c.taskTimer += dt;
    const progress = clamp(c.taskTimer / Math.max(0.2, c.taskDuration), 0, 1);
    const idx = Math.min(t.anims.length - 1, Math.floor(progress * t.anims.length));
    if (idx !== c.taskAnimIndex) { c.taskAnimIndex = idx; c.anim.setState(t.anims[idx]); }
    c.anim.update(dt, { speed: 0, carry: true });
    this._applyPose(c, c.anim.cur);
    if (c.taskTimer > 0.6 && c.props.box) c.props.box.visible = false;
    if (c.taskTimer >= c.taskDuration) {
      this._finishPerform(c);
    }
  }

  _updateCustomerState(c, dt) {
    if (c.state === STATE.WALK_TO_TARGET || c.state === STATE.TURN_TO_TARGET) {
      if (c.state === STATE.WALK_TO_TARGET) this._updateWalk(c, dt);
      else {
        const rate = STORE.turnSpeed * dt;
        const d = wrapAngle(c.faceTarget - c.yaw);
        c.yaw += clamp(d, -rate, rate);
        c.anim.setState('Idle_Stand', { speed: 0 });
        c.anim.update(dt, { speed: 0 });
        this._applyPose(c, c.anim.cur);
        if (Math.abs(d) < 0.06) {
          c.yaw = c.faceTarget;
          const cb = c.afterTurn; c.afterTurn = null;
          if (cb) cb();
        }
      }
      return;
    }
    if (c.state === STATE.CASHIER_SERVICE || c.state === STATE.ASSIST_CUSTOMER) {
      c.serviceTimer += dt;
      const steps = c.tag === 'A'
        ? ['Greet', 'Cashier_Scan', 'Cashier_Bag', 'Talk', 'Idle_Stand']
        : ['Talk', 'Talk', 'Idle_Stand'];
      const stepDur = c.tag === 'A' ? 1.15 : 1.35;
      const idx = Math.min(steps.length - 1, Math.floor(c.serviceTimer / stepDur));
      c.anim.setState(steps[idx]);
      c.anim.update(dt, { speed: 0 });
      this._applyPose(c, c.anim.cur);
      if (c.serviceTimer > steps.length * stepDur) this._finishCustomer(c);
      return;
    }
    this._finishCustomer(c);
  }

  _separateClerks(dt) {
    const a = this.clerks.A; const b = this.clerks.B;
    if (!a || !b) return;
    const dx = b.pos.x - a.pos.x;
    const dz = b.pos.z - a.pos.z;
    const d = Math.hypot(dx, dz);
    const MIN = 0.70;
    if (d < MIN) {
      const nx = d > 1e-4 ? dx / d : 1;
      const nz = d > 1e-4 ? dz / d : 0;
      const push = (MIN - d) * 0.5 + 0.02;
      const tryMove = (c, sign) => {
        const dirs = [[nx * sign, nz * sign], [nz * sign, -nx * sign], [-nz * sign, nx * sign],
          [nx * sign + nz * sign, nz * sign - nx * sign]];
        for (const [ux, uz] of dirs) {
          const L = Math.hypot(ux, uz) || 1;
          const x = c.pos.x + (ux / L) * push;
          const z = c.pos.z + (uz / L) * push;
          if (this.nav.walkable(x, z)) { c.pos.x = x; c.pos.z = z; return true; }
        }
        // last resort: nearest walkable cell
        const near = this.nav.nearestWalkable(c.pos.x + nx * sign * push, c.pos.z + nz * sign * push, 1.2);
        if (near) { c.pos.x = near[0]; c.pos.z = near[1]; return true; }
        return false;
      };
      if (!tryMove(a, -1)) tryMove(b, 1);
      if (!tryMove(b, 1)) tryMove(a, -1);
    }
    // prevent both standing on the same task spot
    if (a.task && b.task && a.task.area === b.task.area) {
      const dd = dist2(a.task.target.x, a.task.target.z, b.task.target.x, b.task.target.z);
      if (dd < 2.0) {
        if (a.state === STATE.SELECT_TASK) a.task = null;
        else if (b.state === STATE.SELECT_TASK) b.task = null;
      }
    }
  }

  // --------------------------------------------------------------------- API
  trigger(tag) {
    if (tag === 'A') { this.notifyCustomer('checkout', 'checkout'); return 'checkout-event'; }
    const c = this.clerks.B;
    if (c) {
      c.forceTaskId = 'restock';
      if (c.state === STATE.SELECT_TASK) { /* next update picks it */ }
      else { this._interruptForTask(c, 'restock'); }
    }
    return 'restock-task';
  }

  _interruptForTask(c, taskId) {
    if (c.carry) this._showBox(c, false);
    if (c.tool) this._showBroom(c, false);
    c.task = null;
    c.interrupted = null;
    c.forceTaskId = taskId;
    this._enterSelect(c);
  }

  debugNav(x, z, tx, tz) {
    return {
      walkable: this.nav.walkable(x, z),
      targetWalkable: tx === undefined ? null : this.nav.walkable(tx, tz),
      nearest: this.nav.nearestWalkable(x, z),
      path: tx === undefined ? null : this.nav.findPath(x, z, tx, tz),
    };
  }

  /** A guaranteed visible camera for screenshots: tries several azimuths, rejects
   * positions inside obstacles or with a blocked line of sight (2D nav test). */
  cameraFor(tag, dist = 3.2, height = 1.85) {
    const c = this.clerks[tag];
    if (!c) return null;
    const p = c.pos;
    const angles = [0, 0.55, -0.55, 1.15, -1.15, 1.8, -1.8, Math.PI * 0.75, -Math.PI * 0.75];
    const los = (x, z) => {
      const n = Math.max(6, Math.ceil(dist / 0.22));
      for (let i = 1; i <= n; i++) {
        const t = i / n;
        if (!this.nav.walkable(p.x + (x - p.x) * t, p.z + (z - p.z) * t)) return false;
      }
      return true;
    };
    for (const a of angles) {
      const x = p.x + Math.sin(c.yaw + Math.PI + a) * dist;
      const z = p.z + Math.cos(c.yaw + Math.PI + a) * dist;
      if (x < -11.9 || x > 11.9 || z < -6.9 || z > 6.8) continue;
      if (!this.nav.walkable(x, z)) continue;
      if (!los(x, z)) continue;
      return { pos: [x, height, z], target: [p.x, 1.0, p.z] };
    }
    // fallback: high behind camera
    return {
      pos: [Math.max(-11.8, Math.min(11.8, p.x - Math.sin(c.yaw) * 2.4)),
        Math.min(3.1, height + 1.0),
        Math.max(-6.8, Math.min(6.8, p.z - Math.cos(c.yaw) * 2.4))],
      target: [p.x, 1.0, p.z],
    };
  }

  forceTask(tag, taskId) {
    const c = this.clerks[tag];
    if (!c) return false;
    if (c.carry) this._showBox(c, false);
    if (c.tool) this._showBroom(c, false);
    c.task = null;
    c.interrupted = null;
    c.customer = null;
    c.forceTaskId = taskId;
    this._enterSelect(c);
    return true;
  }

  setDebug(on) {
    this.debug = !!on;
    if (this._hud) this._hud.style.display = this.debug ? 'block' : 'none';
    return this.debug;
  }

  setCustomerDemo(on) { this.customerDemo = !!on; }

  getState() {
    const out = {};
    ['A', 'B'].forEach((tag) => {
      const c = this.clerks[tag];
      out[tag] = c ? {
        mode: c.state,
        task: c.task ? c.task.id : null,
        position: [c.pos.x, 0, c.pos.z],
      } : null;
    });
    return out;
  }

  getDebugState() {
    const out = {};
    ['A', 'B'].forEach((tag) => {
      const c = this.clerks[tag];
      if (!c) return;
      out[tag] = {
        state: c.state,
        task: c.task ? c.task.id : null,
        taskTarget: c.task ? [c.task.target.x, c.task.target.z] : null,
        taskArea: c.task ? c.task.area : null,
        animation: c.anim.state,
        remaining: c.task ? Math.max(0, Number((c.taskDuration - c.taskTimer).toFixed(2))) : 0,
        customer: c.customer ? c.customer.type : null,
        interrupted: !!c.interrupted,
        position: [Number(c.pos.x.toFixed(2)), 0, Number(c.pos.z.toFixed(2))],
        yaw: Number(c.yaw.toFixed(3)),
        forward: [Number(Math.sin(c.yaw).toFixed(2)), Number(Math.cos(c.yaw).toFixed(2))],
        speed: Number(c.speed.toFixed(2)),
        pathLeft: c.path ? Math.max(0, c.path.length - c.pathIndex) : 0,
        carry: c.carry,
        boxVisible: !!(c.props.box && c.props.box.visible),
        tool: c.tool,
        navOk: this.nav.walkable(c.pos.x, c.pos.z),
        customersServed: c.stats.customersServed || 0,
      };
    });
    return {
      time: Number(this.time.toFixed(1)),
      queue: this.customerQueue.filter((e) => !e.handled).length,
      clerks: out,
      stats: { A: this.clerks.A && this.clerks.A.stats, B: this.clerks.B && this.clerks.B.stats },
      taskCounts: this.tm.stats,
      history: this.tm.history,
      events: { ...this.eventCounts, queue: this.customerQueue.filter((e) => !e.handled).length },
      customersServed: this.customerQueue.filter((e) => e.handled).length,
    };
  }

  _updateHud(dt) {
    if (!this._hud) return;
    if (this.time - this.lastHudUpdate < 0.2) return;
    this.lastHudUpdate = this.time;
    const s = this.getDebugState();
    const rows = ['CLERK DEBUG  [N] toggle   t=' + s.time.toFixed(0) + 's   queue=' + s.queue];
    ['A', 'B'].forEach((tag) => {
      const c = s.clerks[tag];
      rows.push('[' + tag + '] ' + c.state + ' | task ' + (c.task || '-') + ' @' + (c.taskArea || '-'));
      rows.push('    anim ' + c.animation + '  left ' + c.remaining + 's  pos(' + c.position[0] + ',' + c.position[2] + ')');
      rows.push('    cust ' + (c.customer || '-') + '  interrupted ' + (c.interrupted ? 'yes' : 'no') + '  ' + (c.carry ? 'carry' : '') + (c.tool ? ' ' + c.tool : ''));
    });
    this._hud.textContent = rows.join('\n');
  }
}
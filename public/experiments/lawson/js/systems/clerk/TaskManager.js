import { TASKS } from './clerkConfig.js';

const HISTORY_LEN = 4;

function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
function rand(a, b) { return a + Math.random() * (b - a); }

/**
 * Weighted task scheduler shared by both clerks.
 * Weights are dynamic: recency penalty, cooldown, area staleness, distance,
 * mutual exclusion (two clerks never work the same spot) and history.
 */
export class TaskManager {
  constructor() {
    this.now = 0;
    this.history = { A: [], B: [] };
    this.lastDone = { A: {}, B: {} };
    this.cooldownUntil = { A: {}, B: {} };
    this.lastTarget = { A: {}, B: {} };
    this.stats = { A: {}, B: {} };
  }

  tick(dt) { this.now += dt; }

  _targetPenalty(tag, taskId, idx) {
    const last = this.lastTarget[tag][taskId];
    return last === idx ? 0.35 : 1;
  }

  /**
   * Choose a task for a clerk.
   * @param {'A'|'B'} tag
   * @param {{position:{x,z}, other:{tag,taskId,area,target}|null, forceTaskId?:string}} opts
   */
  choose(tag, opts) {
    const list = TASKS[tag] || [];
    const pos = opts.position || { x: 0, z: 0 };
    const other = opts.other || null;
    const candidates = [];

    for (const task of list) {
      if (opts.forceTaskId && task.id !== opts.forceTaskId) continue;
      const cd = this.cooldownUntil[tag][task.id] || -1;
      if (!opts.forceTaskId && this.now < cd) continue;

      for (let ti = 0; ti < task.targets.length; ti++) {
        const target = task.targets[ti];
        // area exclusion: never work in the same spot as the other clerk
        if (other && other.area === target.area) {
          const d = other.target ? Math.hypot(other.target.x - target.x, other.target.z - target.z) : 0;
          if (d < 2.2) continue;
        }
        const dist = Math.hypot(target.x - pos.x, target.z - pos.z);
        let weight = task.weight || 1;

        // history / repetition penalty
        const h = this.history[tag];
        const seen = h.filter((id) => id === task.id).length;
        if (seen > 0) weight *= Math.pow(0.16, seen);
        if (h[h.length - 1] === task.id) weight *= 0.18;

        // staleness / novelty bonus: never-done tasks are strongly preferred
        const last = this.lastDone[tag][task.id];
        const since = last === undefined ? 999 : this.now - last;
        if (last === undefined) weight *= 2.1;
        else weight *= 1 + clamp(since / 45, 0, 1) * 1.1;
        if (since > 60) weight *= 1.25;

        // distance preference (keeps the clerk working locally; restock uses the pickup point)
        const distForTask = task.pickup ? Math.hypot(task.pickup.x - pos.x, task.pickup.z - pos.z) : dist;
        weight *= 1.25 - clamp(distForTask / 20, 0, 1) * 0.55;

        // simultaneous same-task penalty
        if (other && other.taskId === task.id) weight *= 0.18;

        // target variety
        weight *= this._targetPenalty(tag, task.id, ti);

        if (weight > 0) candidates.push({ task, target, ti, weight, dist });
      }
    }
    if (!candidates.length) {
      // fallback: a simple idle task
      const idle = list.find((t) => t.id === 'short_wait' || t.id === 'idle_observe') || list[0];
      return this._instance(tag, idle, idle.targets[0], 0);
    }
    const total = candidates.reduce((s, c) => s + c.weight, 0);
    let r = Math.random() * total;
    for (const c of candidates) {
      r -= c.weight;
      if (r <= 0) return this._instance(tag, c.task, c.target, c.ti);
    }
    const c = candidates[candidates.length - 1];
    return this._instance(tag, c.task, c.target, c.ti);
  }

  _instance(tag, task, target, ti) {
    const dur = rand(task.duration[0], task.duration[1]);
    this.lastTarget[tag][task.id] = ti;
    return {
      id: task.id,
      entryId: this.now + ':' + Math.random().toString(36).slice(2, 7),
      def: task,
      target,
      targetIndex: ti,
      area: target.area,
      duration: dur,
      anims: task.anims,
      pickup: task.pickup || null,
      carry: !!task.carry,
      tool: task.tool || null,
      startedAt: this.now,
    };
  }

  complete(tag, instance) {
    const d = instance.def;
    this.cooldownUntil[tag][d.id] = this.now + (d.cooldown || 20);
    this.lastDone[tag][d.id] = this.now;
    this.history[tag].push(d.id);
    if (this.history[tag].length > HISTORY_LEN) this.history[tag].shift();
    this.stats[tag][d.id] = (this.stats[tag][d.id] || 0) + 1;
  }

  /** returns a possibly resumed task instance (remaining duration), or null */
  peekInterrupted(store, tag) {
    return store[tag] || null;
  }
}
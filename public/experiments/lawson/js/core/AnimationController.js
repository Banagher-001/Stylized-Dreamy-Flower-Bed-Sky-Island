/**
 * Central animation scheduler. Every system registers here so there is exactly one time
 * source (the UpdateLoop delta) and one global pause switch — no scattered timers.
 */
export class AnimationController {
  constructor() {
    this.systems = [];
    this.mixers = [];
    this.paused = false;
  }

  register(system) {
    if (system && typeof system.update === 'function') this.systems.push(system);
    return system;
  }

  addMixer(mixer) {
    this.mixers.push(mixer);
    return mixer;
  }

  setPaused(v) {
    this.paused = !!v;
  }

  update(dt, elapsed) {
    const d = this.paused ? 0 : dt;
    for (const sys of this.systems) {
      try {
        sys.update(d, elapsed);
      } catch (err) {
        console.error('[AnimationController] system failed:', sys.constructor && sys.constructor.name, err);
      }
    }
    if (d > 0) {
      for (const m of this.mixers) m.update(d);
    }
  }
}

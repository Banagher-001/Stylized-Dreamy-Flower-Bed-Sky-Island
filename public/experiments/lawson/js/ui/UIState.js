/** Single source of truth for UI-visible state (avoid duplicated state per module). */
export class UIState {
  constructor() {
    this.state = {
      loaded: false,
      paused: false,
      quality: 'high',
      cameraMode: 'orbit',
      timeOfDay: 18.5,
      roofVisible: true,
      lights: {},
      traffic: { running: false, current: 'A', phase: 'IDLE', speed: 1 },
      doors: { automatic: true, isOpen: false },
      walk: false,
      fps: 0,
      stats: { drawCalls: 0, triangles: 0 },
    };
    this.listeners = new Set();
  }

  patch(partial) {
    Object.assign(this.state, partial);
    this.emit();
  }

  subscribe(fn) {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  emit() {
    for (const fn of this.listeners) {
      try { fn(this.state); } catch (err) { console.error('[UIState] listener failed', err); }
    }
  }
}

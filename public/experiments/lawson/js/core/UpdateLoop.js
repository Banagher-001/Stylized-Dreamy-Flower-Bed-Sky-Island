/** rAF loop with clamped delta time, FPS sampling and a global speed factor. */
export class UpdateLoop {
  constructor(onFrame) {
    this.onFrame = onFrame;
    this.running = false;
    this.last = 0;
    this.elapsed = 0;
    this.fps = 0;
    this._fpsAccum = 0;
    this._fpsFrames = 0;
    this.speed = 1.0;
    this.paused = false;
    this._raf = 0;
    this._tick = this._tick.bind(this);
    document.addEventListener('visibilitychange', () => {
      // avoid a huge delta after the tab was hidden
      this.last = performance.now();
    });
  }

  start() {
    if (this.running) return;
    this.running = true;
    this.last = performance.now();
    this._raf = requestAnimationFrame(this._tick);
  }

  stop() {
    this.running = false;
    cancelAnimationFrame(this._raf);
  }

  _tick(now) {
    if (!this.running) return;
    let dt = (now - this.last) / 1000;
    this.last = now;
    if (!isFinite(dt) || dt < 0) dt = 0;
    dt = Math.min(dt, 0.1);
    this.elapsed += dt;
    this._fpsAccum += dt;
    this._fpsFrames += 1;
    if (this._fpsAccum >= 0.5) {
      this.fps = Math.round(this._fpsFrames / this._fpsAccum);
      this._fpsAccum = 0;
      this._fpsFrames = 0;
    }
    const scaled = this.paused ? 0 : dt * this.speed;
    this.onFrame(scaled, dt, this.elapsed);
    this._raf = requestAnimationFrame(this._tick);
  }
}

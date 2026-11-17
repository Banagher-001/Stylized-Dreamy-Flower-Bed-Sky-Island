import { clamp } from './dom';

export type TrackDirection = -1 | 1;
export type WheelAxis = 'horizontal' | 'vertical';
export const cardWheelMotion = { baseSpeed: 28, maxSpeed: 560, response: .07, hold: 80, decay: 140, stopSpeed: 1.5 } as const;

/** CSS pixels only: browser zoom/DPR never multiplies a wheel delta. */
export function normalizeCardWheel(event: Pick<WheelEvent, 'deltaX' | 'deltaY' | 'deltaMode' | 'shiftKey'>, lineHeight: number, pageWidth: number) {
  const unit = event.deltaMode === 1 ? lineHeight : event.deltaMode === 2 ? pageWidth : 1;
  let x = Number.isFinite(event.deltaX) ? clamp(event.deltaX * unit, -1200, 1200) : 0;
  let y = Number.isFinite(event.deltaY) ? clamp(event.deltaY * unit, -1200, 1200) : 0;
  if (event.shiftKey && !x) { x = y;y = 0; }
  return { x, y };
}

/** One axis per gesture; no timer or animation loop of its own. */
export function createWheelGesture() {
  let axis: WheelAxis | undefined, last = -Infinity;
  return {
    take(x: number, y: number, now: number): WheelAxis | undefined {
      if (!x && !y) return axis;
      if (now - last > 180) axis = undefined;
      last = now;
      axis ??= Math.abs(x) > Math.abs(y) ? 'horizontal' : 'vertical';
      return axis;
    },
    clear() { axis = undefined;last = -Infinity; },
  };
}

/** Recent input sets a bounded velocity target, never an accumulating impulse. */
export function createWheelVelocity() {
  let samples: { time: number; amount: number }[] = [];
  let last = -Infinity, strength = 0, inputDirection: TrackDirection = 1;
  let released = false;
  return {
    push(delta: number, now: number): TrackDirection | undefined {
      if (!Number.isFinite(delta) || Math.abs(delta) < .1) return undefined;
      const direction: TrackDirection = delta > 0 ? 1 : -1;
      // Tiny opposite trackpad tail samples must not reverse a deliberate gesture.
      if (direction !== inputDirection && Math.abs(delta) < 1.5 && now - last < 140) return undefined;
      if (direction !== inputDirection || now - last > 180 || released) samples = [];
      inputDirection = direction;released = false;
      samples = samples.filter(sample => now - sample.time <= 100);
      samples.push({ time: now, amount: Math.abs(delta) });
      // A single first event gets a full 100 ms window, with no division by zero.
      const rate = samples.reduce((total, sample) => total + sample.amount, 0) * 10;
      strength = clamp(rate * .23, 0, cardWheelMotion.maxSpeed);last = now;
      return direction;
    },
    target(now: number, base: number) {
      const age = now - last;
      const extra = strength * Math.exp(-Math.max(0, age - (released ? 0 : cardWheelMotion.hold)) / (released ? 90 : cardWheelMotion.decay));
      if (extra < cardWheelMotion.stopSpeed) { this.clear();return { speed: base, active: false }; }
      return { speed: clamp(base + inputDirection * extra, -cardWheelMotion.maxSpeed, cardWheelMotion.maxSpeed), active: true };
    },
    release(now: number) {
      if (!strength) return;
      strength *= Math.exp(-Math.max(0, now - last - cardWheelMotion.hold) / cardWheelMotion.decay);
      last = now;released = true;samples = [];
    },
    clear() { samples = [];last = -Infinity;strength = 0;released = false; },
  };
}

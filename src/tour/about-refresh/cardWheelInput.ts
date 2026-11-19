import { clamp } from './dom';

export type TrackDirection = -1 | 1;
export type WheelAxis = 'horizontal' | 'vertical';
export const cardWheelMotion = { baseSpeed: 28, maxSpeed: 560, response: .06, hold: 80, settle: 200 } as const;

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
  let settleAt = -Infinity;
  let settleFrom: number | undefined;

  function clear() {
    samples = [];
    last = settleAt = -Infinity;
    strength = 0;
    settleFrom = undefined;
  }

  return {
    get active() { return strength > 0; },
    push(delta: number, now: number): TrackDirection | undefined {
      if (!Number.isFinite(delta) || Math.abs(delta) < .1) return undefined;
      const direction: TrackDirection = delta > 0 ? 1 : -1;
      // Tiny opposite trackpad tail samples must not reverse a deliberate gesture.
      if (direction !== inputDirection && Math.abs(delta) < 1.5 && now - last < 140) return undefined;
      if (direction !== inputDirection || now - last > 180) samples = [];
      inputDirection = direction;
      samples = samples.filter(sample => now - sample.time <= 100);
      samples.push({ time: now, amount: Math.abs(delta) });
      // A single first event gets a full 100 ms window, with no division by zero.
      const rate = samples.reduce((total, sample) => total + sample.amount, 0) * 10;
      strength = clamp(rate * .23, 0, cardWheelMotion.maxSpeed);
      last = now;
      settleAt = now + cardWheelMotion.hold;
      settleFrom = undefined;
      return direction;
    },
    target(now: number, base: number, velocity: number) {
      if (!strength) return { speed: base, active: false, settling: false };
      if (now <= settleAt) {
        return { speed: clamp(base + inputDirection * strength, -cardWheelMotion.maxSpeed, cardWheelMotion.maxSpeed), active: true, settling: false };
      }
      // Start the tail at the speed actually reached. A second velocity filter
      // here would keep the cards moving long after the end of the tail.
      const t = clamp((now - settleAt) / cardWheelMotion.settle, 0, 1);
      const remaining = 1 - t * t * (3 - 2 * t);
      settleFrom ??= velocity;
      const speed = base + (settleFrom - base) * remaining;
      if (t === 1) clear();
      return { speed, active: t < 1, settling: true };
    },
    release(now: number) {
      if (!strength) return;
      settleAt = Math.min(settleAt, now);
      samples = [];
    },
    clear,
  };
}

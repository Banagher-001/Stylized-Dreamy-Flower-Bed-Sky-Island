import { waterConfig } from '../config/water';

/** Pure clock: clamps stalls, does not advance while paused, and can be tested without DOM. */
export function createAnimationClock(initialTime: number, maxDelta = waterConfig.maxFrameDelta) {
  let time = initialTime;
  let previous: number | null = null;
  return {
    get time() { return time; },
    resetTimestamp() { previous = null; },
    tick(timestamp: number, playing: boolean) {
      const delta = previous === null ? 0 : Math.min(maxDelta, Math.max(0, (timestamp - previous) / 1000));
      previous = timestamp;
      if (playing) time += delta;
      return time;
    },
  };
}

export interface AnimationState { playing: boolean; hidden: boolean; reducedMotion: boolean; }

export function createAnimationController(onChange: (state: AnimationState) => void, initialTime: number, initiallyPaused = false, options: { retainReducedPause?: boolean } = {}) {
  const media = window.matchMedia('(prefers-reduced-motion: reduce)');
  const clock = createAnimationClock(initialTime);
  let manualPaused: boolean | null = initiallyPaused || (options.retainReducedPause && media.matches) ? true : null;
  let disposed = false;
  function state(): AnimationState {
    return { playing: !document.hidden && !(manualPaused ?? media.matches), hidden: document.hidden, reducedMotion: media.matches };
  }
  function notify() {
    if (disposed) return;
    clock.resetTimestamp();
    onChange(state());
  }
  function mediaChanged() {
    if (media.matches && manualPaused !== true) manualPaused = options.retainReducedPause ? true : null;
    notify();
  }
  document.addEventListener('visibilitychange', notify);
  media.addEventListener('change', mediaChanged);
  return {
    get state() { return state(); },
    get time() { return clock.time; },
    advance(timestamp: number) { return clock.tick(timestamp, state().playing); },
    resetTimestamp: clock.resetTimestamp,
    toggle() { manualPaused = !(manualPaused ?? media.matches); notify(); },
    dispose() {
      if (disposed) return;
      disposed = true;
      document.removeEventListener('visibilitychange', notify);
      media.removeEventListener('change', mediaChanged);
    },
  };
}

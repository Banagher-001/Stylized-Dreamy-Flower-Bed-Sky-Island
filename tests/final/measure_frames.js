// Paste this function into DevTools, then call await measureCourtyardFrames().
// Keep the page visible, play the scene and warm it for 5 seconds first.
async function measureCourtyardFrames(durationMs = 60000) {
  if (document.hidden || document.querySelector('#scene-host')?.dataset.motionState !== 'running') {
    throw new Error('Keep the scene visible and playing before measuring.');
  }
  const original = window.requestAnimationFrame;
  const intervals = [];
  let active = true, count = 0, previous = 0, changedVisibility = false;
  const onVisibility = () => { changedVisibility = true; };
  document.addEventListener('visibilitychange', onVisibility);
  window.requestAnimationFrame = function (callback) {
    return original.call(window, (timestamp) => {
      if (active) {
        const now = performance.now();
        if (previous) intervals.push(now - previous);
        previous = now;count++;
      }
      callback(timestamp);
    });
  };
  const start = performance.now();
  try {
    await new Promise(resolve => setTimeout(resolve, durationMs));
    const elapsed = performance.now() - start;
    intervals.sort((a, b) => a - b);
    const canvas = document.querySelector('canvas');
    return {
      measuredAt: new Date().toISOString(),
      validVisibleSession: !changedVisibility,
      browser: navigator.userAgent,
      mode: canvas?.dataset.renderMode,
      output: canvas ? [canvas.width, canvas.height] : null,
      sample: canvas ? [Number(canvas.dataset.sampleWidth), Number(canvas.dataset.sampleHeight)] : null,
      elapsedMs: elapsed,
      frames: count,
      meanFPS: count * 1000 / elapsed,
      p95IntervalMs: intervals[Math.min(intervals.length - 1, Math.floor(intervals.length * 0.95))] ?? null,
      longestIntervalMs: intervals.at(-1) ?? null,
      intervalsOver100ms: intervals.filter(value => value > 100).length,
      note: 'Application RAF callbacks; device model/GPU/power/refresh rate must be recorded separately. This script does not animate the scene itself.',
    };
  } finally {
    active = false;
    window.requestAnimationFrame = original;
    document.removeEventListener('visibilitychange', onVisibility);
  }
}
